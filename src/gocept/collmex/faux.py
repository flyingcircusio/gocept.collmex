"""A faux Collmex server for tests.

This module implements a WSGI application that mimics the parts of the
Collmex HTTP interface used by ``gocept.collmex`` and its test suite:

* the data exchange CGI endpoint (CSV import/export), and
* the HTML pages used by ``browser_login()`` and the browser-based test
  helpers (delete company data, create projects and employees).

Data is held in memory, so the server can be shipped with
``gocept.collmex`` and dependent projects can run their tests without
access to, and without contending for, the Collmex test system.

"""

import configparser
import csv
import datetime
import io
import os
import socketserver
import tempfile
import threading
import wsgiref.simple_server

import pytest
import webob

import gocept.collmex.model
import gocept.collmex.utils
from gocept.collmex.collmex import CollmexDialect

NULL = "(NULL)"
ENCODING = "windows-1252"

INI_TEMPLATE = """\
[credentials]
customer_id = 10001
company_id = 1
username = testuser
password = testpassword

[test-credentials]
customer_id = 10001
company_id = 1
username = testuser
password = testpassword
"""

KINDS = (
    "customers",
    "products",
    "product_groups",
    "members",
    "abos",
    "agreements",
    "invoices",
    "activities",
)


class Store:
    """In-memory storage for the faux server.

    Rows are stored exactly as the client sent them (full field width),
    together with the time they were added -- the latter powers the
    "Nur geänderte" (only changed) watermark emulation.
    """

    def __init__(self):
        # RLock: handlers are nested (get_projects -> find_customer).
        self.lock = threading.RLock()
        self.reset()

    def reset(self):
        """Wipes all data, just like deleting the company in the UI."""
        with self.lock:
            self.rows = {kind: [] for kind in KINDS}
            self.projects = {}  # number -> dict, see project_form()
            self.employees = {}  # number -> dict(vorname, name)
            self.next_employee_nr = 1
            self.next_project_nr = 1
            self.pending_project = None
            # Watermarks for the "Nur geänderte" mechanism, keyed by
            # (Systemname, GET satzart):
            self.watermarks = {}
            self.failed_logins = 0
            # Every company has a generic customer, numbered 9999:
            generic = gocept.collmex.model.Customer()
            generic["Kundennummer"] = "9999"
            generic["Firma Nr"] = "1"
            generic["Firma"] = "Allgemeiner Geschäftspartner"
            self.add("customers", list(generic))

    def add(self, kind, row):
        with self.lock:
            self.rows[kind].append([list(row), datetime.datetime.now()])

    def all(self, kind):
        with self.lock:
            return [(list(row), changed) for row, changed in self.rows[kind]]


def parse_number(value):
    """Parses a Collmex number ("5", "5.00" or "9,65") into a float."""
    return float(str(value).replace(",", ".") or 0)


def format_number(value):
    """Formats a float the way Collmex exports it ("9,65")."""
    return f"{value:.2f}".replace(".", ",")


def format_date(value):
    """Normalises "2012-01-01" / "20120101" to the exported "20120101"."""
    value = str(value)
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.datetime.strptime(value, fmt).strftime("%Y%m%d")
        except ValueError:
            pass
    raise ValueError(f"Unparsable date: {value!r}")


def format_time(value):
    """Normalises "08:07:00" / "08:07" to the exported "08:07"."""
    hour, minute = str(value).split(":")[:2]
    return f"{int(hour):02d}:{int(minute):02d}"


def is_set(value):
    """Tells whether a CSV field carries an actual filter value."""
    return value not in (None, "", NULL)


def _parse_datetime(value, formats):
    value = str(value)
    for fmt in formats:
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unparsable date/time: {value!r}")


class FauxError(Exception):
    """An error to be reported to the client as MESSAGE record."""

    def __init__(self, code, text):
        super().__init__(code, text)
        self.code = code
        self.text = text


class FauxCollmex:
    """WSGI application mimicking the Collmex HTTP interface."""

    def __init__(self, credentials, store=None):
        self.username = credentials["username"]
        self.password = credentials["password"]
        self.company_id = credentials.get("company_id", "1")
        self.store = store if store is not None else Store()

    # -- WSGI ----------------------------------------------------------

    def __call__(self, environ, start_response):
        request = webob.Request(environ)
        if request.path == "/cgi-bin/cgi.exe":
            response = self.handle_api(request)
        else:
            response = self.handle_ui(request)
        return response(environ, start_response)

    # -- CSV API -------------------------------------------------------

    def handle_api(self, request):
        upload = request.POST["fileName"]
        data = upload.file.read() if hasattr(upload, "file") else upload
        if isinstance(data, bytes):
            data = data.decode(ENCODING)
        lines = list(csv.reader(io.StringIO(data), dialect=CollmexDialect))

        if lines[0][:3] != ["LOGIN", self.username, self.password]:
            self.store.failed_logins += 1
            return self.csv_response(
                [],
                status="E",
                code="101004",
                text="Benutzer oder Kennwort nicht korrekt",
            )
        self.store.failed_logins = 0

        try:
            rows = []
            for line in lines[1:]:
                rows.extend(self.process_record(line))
        except FauxError as error:
            return self.csv_response(
                [], status="E", code=error.code, text=error.text
            )
        return self.csv_response(rows)

    def process_record(self, line):
        handler = {
            "CMXINV": self.create_record,
            "CMXKND": self.create_record,
            "CMXPRD": self.create_record,
            "PRDGRP": self.create_product_group,
            "CMXMGD": self.create_record,
            "CMXABO": self.create_record,
            "CMXCAG": self.create_record,
            "CMXACT": self.create_activity,
            "INVOICE_GET": self.get_invoices,
            "CUSTOMER_GET": self.get_customers,
            "MEMBER_GET": self.get_members,
            "PRODUCT_GET": self.get_products,
            "PRODUCT_GROUPS_GET": self.get_product_groups,
            "CUSTOMER_AGREEMENT_GET": self.get_agreements,
            "PROJECT_GET": self.get_projects,
            "ACTIVITIES_GET": self.get_activities,
        }.get(line[0])
        if handler is None:
            raise FauxError("105001", f"Satzart nicht definiert: {line[0]}")
        return handler(line)

    def csv_response(
        self,
        rows,
        status="S",
        code="306000",
        text="Daten wurden erfolgreich übertragen",
    ):
        out = io.StringIO()
        writer = csv.writer(out, dialect=CollmexDialect)
        for row in rows:
            writer.writerow(["" if value is None else value for value in row])
        writer.writerow(["MESSAGE", status, code, text])
        return webob.Response(
            body=out.getvalue().encode(ENCODING),
            content_type="text/csv",
            charset=ENCODING,
        )

    def only_changed(self, line, value_index, systemname_index, satzart):
        """Applies the "Nur geänderte" (only changed) mechanism.

        Returns a filter based on the watermark previously stored for
        the system name, and advances the watermark just like Collmex
        does -- regardless of whether the caller processes the result.
        """
        systemname = line[systemname_index]
        watermark = self.store.watermarks.get((systemname, satzart))
        self.store.watermarks[(systemname, satzart)] = datetime.datetime.now()
        if not is_set(line[value_index]):
            return lambda changed: True
        return lambda changed: watermark is None or changed >= watermark

    def create_record(self, line):
        kind = {
            "CMXKND": "customers",
            "CMXPRD": "products",
            "PRDGRP": "product_groups",
            "CMXMGD": "members",
            "CMXABO": "abos",
            "CMXCAG": "agreements",
            "CMXINV": "invoices",
        }[line[0]]
        # Records with an existing key are replaced:
        key_index = {
            "customers": 1,
            "products": 1,
            "product_groups": 1,
            "members": 1,
            "agreements": 2,
        }.get(kind)
        if key_index is not None and len(line) > key_index:
            self.store.rows[kind] = [
                [row, changed]
                for row, changed in self.store.rows[kind]
                if row[key_index] != line[key_index]
            ]
        self.store.add(kind, line)
        return []

    def create_product_group(self, line):
        # 'Untergruppe von' is an integer reference to an existing
        # parent product group; non-numeric values are silently
        # dropped (Collmex API docs, "Produktgruppe anlegen"):
        if len(line) > 3 and not line[3].isdigit():
            line[3] = ""
        return self.create_record(line)

    def create_activity(self, line):
        self.store.add("activities", line)
        return []

    def get_invoices(self, line):
        # INVOICE_GET;Rechnungsnummer;Firma;Kunde;Von;Bis;Nur
        # ausgegebene;Rueckgabe-Format;Nur geaenderte;Systemname
        changed_filter = self.only_changed(line, 8, 9, "INVOICE_GET")
        result = []
        for row, changed in self.store.all("invoices"):
            if not changed_filter(changed):
                continue
            if is_set(line[1]) and row[1] != line[1]:
                continue
            if is_set(line[3]) and row[6] != line[3]:
                continue
            if is_set(line[4]) or is_set(line[5]):
                # Without an explicitly set date, Collmex uses the
                # creation date:
                date = (
                    row[29] if is_set(row[29]) else changed.strftime("%Y%m%d")
                )
                if is_set(line[4]) and date < line[4]:
                    continue
                if is_set(line[5]) and date > line[5]:
                    continue
            result.append(row)
        return result

    def get_customers(self, line):
        # CUSTOMER_GET;Kundennummer;Firma;Text;...
        result = []
        for row, _ in self.store.all("customers"):
            if is_set(line[1]) and row[1] != line[1]:
                continue
            if is_set(line[3]) and line[3] not in row[7]:
                continue
            result.append(row)
        return result

    def get_members(self, line):
        # MEMBER_GET;Mitgliedsnummer;Firma;Text;...
        result = []
        for row, _ in self.store.all("members"):
            if is_set(line[1]) and row[1] != line[1]:
                continue
            if is_set(line[3]) and line[3] not in row[5]:
                continue
            result.append(row)
        return result

    def get_products(self, line):
        # PRODUCT_GET;Firma;Produktnummer;Produktgruppe;Preisgruppe;...
        result = []
        for row, _ in self.store.all("products"):
            if is_set(line[2]) and row[1] != line[2]:
                continue
            if is_set(line[3]) and row[5] != line[3]:
                continue
            if is_set(line[4]) and row[13] != line[4]:
                continue
            result.append(row)
        return result

    def get_product_groups(self, line):
        # PRODUCT_GROUPS_GET takes no query parameters beyond the
        # satzart (Collmex API docs, "Produktgruppen abfragen").
        return [row for row, _ in self.store.all("product_groups")]

    def get_agreements(self, line):
        # CUSTOMER_AGREEMENT_GET;Firma;Kunde;Produkt;...
        result = []
        for row, _ in self.store.all("agreements"):
            if is_set(line[2]) and row[2] != line[2]:
                continue
            if is_set(line[3]) and row[3] != line[3]:
                continue
            result.append(row)
        return result

    def get_projects(self, line):
        # PROJECT_GET;Projektnummer;Firma;Kunde
        result = []
        with self.store.lock:
            numbers = sorted(self.store.projects, key=int)
            for number in numbers:
                project = self.store.projects[number]
                if is_set(line[1]) and number != line[1]:
                    continue
                if is_set(line[3]) and project["kundeNr"] != line[3]:
                    continue
                for satz_nr in sorted(project["rates"], key=int):
                    result.append(self.project_row(project, number, satz_nr))
        return result

    def project_row(self, project, number, satz_nr):
        rate = project["rates"][satz_nr]
        customer = self.find_customer(project["kundeNr"])
        return [
            "CMXPRJ",
            number,
            self.company_id,
            project["bezeichnung"],
            project["kundeNr"],
            customer[7] if customer else "",  # Name des Kunden
            NULL,  # Abgeschlossen
            format_number(project["budget"]),
            format_number(self.project_worth(project, number)),
            NULL,
            NULL,
            NULL,
            satz_nr,
            NULL,  # Satz Bezeichnung
            rate["produktnummer"],
            rate["satz"],
            "EUR",
            NULL,  # Mengeneinheit
            "0",  # Inaktiv
        ]

    def project_worth(self, project, number):
        """Sums up the value of all activities of a project."""
        total = 0.0
        for row, _ in self.store.all("activities"):
            if row[1] != number:
                continue
            rate = project["rates"].get(row[4])
            if rate is None:
                continue
            start = _parse_datetime(row[7], ("%H:%M:%S", "%H:%M"))
            end = _parse_datetime(row[8], ("%H:%M:%S", "%H:%M"))
            pause_hour, pause_minute = str(row[9]).split(":")[:2]
            duration = (
                end
                - start
                - datetime.timedelta(
                    hours=int(pause_hour), minutes=int(pause_minute)
                )
            )
            total += (
                duration.total_seconds() / 3600.0 * parse_number(rate["satz"])
            )
        return total

    def get_activities(self, line):
        # ACTIVITIES_GET;Projekt;Firma;Mitarbeiter;Von;Bis;Nur nicht
        # abgerechnete;Verrechenbar;Nur interne;Nur geaenderte;Systemname
        changed_filter = self.only_changed(line, 9, 10, "ACTIVITIES_GET")
        result = []
        for row, changed in self.store.all("activities"):
            if not changed_filter(changed):
                continue
            if is_set(line[1]) and row[1] != line[1]:
                continue
            if is_set(line[3]) and row[2] != line[3]:
                continue
            if is_set(line[4]) or is_set(line[5]):
                date = format_date(row[6])
                if is_set(line[4]) and date < line[4]:
                    continue
                if is_set(line[5]) and date > line[5]:
                    continue
            result.append(self.activity_row(row))
        return result

    def activity_row(self, row):
        """Normalises a stored CMXACT row to the exported format."""
        row = list(row)
        project = self.store.projects.get(row[1])
        employee = self.store.employees.get(row[2])
        if project is not None:
            row[1] = "{} {}".format(row[1], project["bezeichnung"])
            rate = project["rates"].get(row[4])
            row[10] = rate["produktnummer"] if rate else ""
        if employee is not None:
            row[2] = "{} {} {}".format(
                row[2],
                employee["vorname"],
                employee["name"],
            )
        row[6] = format_date(row[6])
        row[7] = format_time(row[7])
        row[8] = format_time(row[8])
        row[9] = format_time(row[9])  # Pausen
        row[11] = ""  # In Rechnung Nr
        return row

    def find_customer(self, kundennummer):
        for row, _ in self.store.all("customers"):
            if row[1] == kundennummer:
                return row
        return None

    def find_product(self, produktnummer):
        for row, _ in self.store.all("products"):
            if row[1] == produktnummer:
                return row
        return None

    # -- HTML UI -------------------------------------------------------

    def handle_ui(self, request):
        params = request.POST
        path = request.path
        if path == "/":
            if "group_benutzerId" in params:
                return self.login(params)
            # Step 1 (enter customer id) or step 2 (enter credentials):
            return self.login_form(step=2 if "Kunde" in params else 1)
        if path == "/verwaltung":
            return self.page('<p><a href="/loeschen">Löschen</a></p>')
        if path == "/loeschen":
            if request.method == "POST":
                return self.delete_company(params)
            return self.delete_form()
        if path == "/crm":
            return self.page('<p><a href="/pjcr">Anlegen</a></p>')
        if path == "/pjcr":
            return self.project_form(params)
        if path == "/c.cmx":
            return self.page(
                '<p><a href="/mitarbeiter">Mitarbeiter anlegen</a></p>'
            )
        if path == "/mitarbeiter":
            return self.employee_form(params)
        if path.endswith(",vbrp"):
            return self.page("<h1>Projekt-Verbrauch</h1>")
        return self.page("<h1>Seite nicht gefunden</h1>", status=404)

    NAV = """
<p>
<a href="/verwaltung">Verwaltung</a>
<a href="/crm">Verkauf</a>
<a href="/c.cmx">Buchhaltung</a>
<a href="/x,vbrp">Projekt-Verbrauch</a>
</p>
"""

    def page(self, body, status=200, nav=True):
        content = self.NAV + body if nav else body
        return webob.Response(
            body=(
                f'<html><head><meta charset="{ENCODING}"></head>'
                f"<body>{content}</body></html>"
            ).encode(ENCODING),
            status=status,
            content_type="text/html",
            charset=ENCODING,
        )

    def login_form(self, step=1, error=None):
        error_markup = ""
        if error:
            error_markup = '<p class="error">%s</p>' % error
        if step == 1:
            form = """
<form method="POST">
<input name="Kunde">
<button type="submit">Weiter</button>
</form>
"""
        else:
            form = """
<form method="POST">
<input name="group_benutzerId">
<input name="group_kennwort" type="password">
<button type="submit">Login</button>
</form>
"""
        return self.page("%s\n%s" % (error_markup, form), nav=False)

    def login(self, params):
        if (
            params["group_benutzerId"] == self.username
            and params["group_kennwort"] == self.password
        ):
            self.store.failed_logins = 0
            return self.page("<h1>Angemeldet</h1>")
        self.store.failed_logins += 1
        return self.login_form(
            step=2, error="Benutzer oder Kennwort nicht korrekt"
        )

    def delete_form(self):
        return self.page("""
<form method="POST">
<input type="radio" name="group_loeschArt" value="1" checked>Nur Daten
<input type="radio" name="group_loeschArt" value="2">Daten und Struktur
<input type="checkbox" name="group_bestaetigung" value="1">Bestätigung
<button type="submit" name="loeschen" value="Firma löschen">Löschen</button>
</form>
""")

    def delete_company(self, params):
        if "group_bestaetigung" not in params:
            return self.page(
                '<p class="error">Bestätigung fehlt</p>' + "<p>Abgebrochen"
            )
        self.store.reset()
        return self.page("<p>Daten erfolgreich gelöscht</p>")

    def find_agreement_price(self, kunde_nr, produktnummer):
        """Returns the price of a customer agreement, if one exists.

        Customer agreements override the product's base price when
        Collmex computes project rates.
        """
        candidates = [
            row
            for row, _ in self.store.all("agreements")
            if row[2] == kunde_nr and row[3] == produktnummer
        ]
        if not candidates:
            return None
        return parse_number(candidates[-1][7])  # Preis

    def rate_price(self, kunde_nr, produktnummer, product):
        price = self.find_agreement_price(kunde_nr, produktnummer)
        if price is None:
            price = parse_number(product[14])  # Verkaufs-Preis
        return format_number(price)

    def project_form(self, params):
        store = self.store
        if not params:
            return self.page("""
<form method="POST">
<button type="submit" name="anlegen" value="1">Anlegen</button>
</form>
""")
        if "anlegen" in params:
            return self.page("""
<form method="POST">
<input name="group_bezeichnung">
<input name="group_kundeNr" value="10000">
<input name="table_1_produktNr">
<input name="group_budget" value="0">
<button type="submit" name="speichern" value="1">Speichern</button>
</form>
""")
        if "group_bezeichnung" in params:
            # Step 1: create project with rate 1.
            produktnummer = params["table_1_produktNr"]
            product = self.find_product(produktnummer)
            if product is None:
                return self.page(
                    f'<p class="error">Produkt {produktnummer} existiert nicht</p>'
                )
            number = str(store.next_project_nr)
            store.next_project_nr += 1
            project = {
                "bezeichnung": params["group_bezeichnung"],
                "kundeNr": params["group_kundeNr"],
                "budget": parse_number(params["group_budget"]),
                "rates": {
                    "1": {
                        "produktnummer": produktnummer,
                        "satz": self.rate_price(
                            params["group_kundeNr"], produktnummer, product
                        ),
                    },
                },
            }
            with store.lock:
                store.projects[number] = project
                store.pending_project = project
            return self.page("""
<form method="POST">
<input name="table_2_produktNr">
<button type="submit" name="speichern" value="2">Speichern</button>
</form>
""")
        if "table_2_produktNr" in params:
            # Step 2: configure product of rate 2.
            produktnummer = params["table_2_produktNr"]
            product = self.find_product(produktnummer)
            if product is None:
                return self.page(
                    f'<p class="error">Produkt {produktnummer} existiert nicht</p>'
                )
            kunde_nr = store.pending_project["kundeNr"]
            store.pending_project["rates"]["2"] = {
                "produktnummer": produktnummer,
                "satz": self.rate_price(kunde_nr, produktnummer, product),
            }
            return self.page(
                """
<form method="POST">
<input name="table_2_satz" value="{}">
<button type="submit" name="speichern" value="3">Speichern</button>
</form>
""".format(store.pending_project["rates"]["2"]["satz"])
            )
        if "table_2_satz" in params:
            # Step 3: set price of rate 2.
            rate = store.pending_project["rates"]["2"]
            rate["satz"] = format_number(parse_number(params["table_2_satz"]))
            store.pending_project = None
            return self.page("<p>Gespeichert</p>")
        return self.page('<p class="error">Unbekannter Schritt</p>')

    def employee_form(self, params):
        store = self.store
        if not params:
            return self.page("""
<form method="POST">
<button type="submit" name="anlegen" value="1">Anlegen</button>
</form>
""")
        if "anlegen" in params:
            return self.page("""
<form method="POST">
<input name="group_adrVorname">
<input name="group_adrName">
<button type="submit" name="speichern" value="1">Speichern</button>
</form>
""")
        if "group_adrName" in params:
            with store.lock:
                for number, employee in store.employees.items():
                    if (
                        employee["vorname"] == params["group_adrVorname"]
                        and employee["name"] == params["group_adrName"]
                    ):
                        break
                else:
                    number = str(store.next_employee_nr)
                    store.next_employee_nr += 1
                store.employees[number] = {
                    "vorname": params["group_adrVorname"],
                    "name": params["group_adrName"],
                }
            return self.page("<p>Mitarbeiter gespeichert</p>")
        return self.page('<p class="error">Unbekannter Schritt</p>')


# -- Server plumbing ---------------------------------------------------


class QuietHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


class ThreadedWSGIServer(
    socketserver.ThreadingMixIn, wsgiref.simple_server.WSGIServer
):
    daemon_threads = True


def read_credentials():
    """Reads the credentials the faux server validates logins against."""
    parser = configparser.ConfigParser()
    ini_file = os.environ.get(
        "COLLMEX_INI",
        gocept.collmex.utils._find_ini_file_from_current_directory(),
    )
    if ini_file and os.path.isfile(ini_file):
        with open(ini_file) as f:
            parser.read_file(f)
    for section in ("test-credentials", "credentials"):
        if parser.has_section(section):
            return dict(parser.items(section))
    # No ini file anywhere: fall back to the same dummy credentials
    # written by ensure_ini_file() below.
    return {
        "customer_id": "10001",
        "company_id": "1",
        "username": "testuser",
        "password": "testpassword",
    }


def start_server(credentials=None, store=None):
    """Starts a faux Collmex server on a local port.

    Returns the server object; its ``url`` attribute points to the
    server, and is suitable for ``COLLMEX_API_URL``.
    """
    app = FauxCollmex(credentials or read_credentials(), store)
    server = wsgiref.simple_server.make_server(
        "127.0.0.1",
        0,
        app,
        server_class=ThreadedWSGIServer,
        handler_class=QuietHandler,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    server.url = "http://127.0.0.1:%d" % server.server_port
    return server


def stop_server(server):
    server.shutdown()
    server.server_close()


# -- pytest fixture ----------------------------------------------------


def _ensure_ini_file(saved_env):
    """Points COLLMEX_INI at a dummy file if none can be found.

    The faux server does not need real credentials, but constructing
    ``Collmex`` objects does (they are read from collmex.ini). The
    original value is remembered in `saved_env` so the fixture can
    restore it.
    """
    ini_file = os.environ.get(
        "COLLMEX_INI",
        gocept.collmex.utils._find_ini_file_from_current_directory(),
    )
    if ini_file and os.path.isfile(ini_file):
        return
    handle, path = tempfile.mkstemp(prefix="collmex", suffix=".ini")
    with os.fdopen(handle, "w") as f:
        f.write(INI_TEMPLATE)
    saved_env.setdefault("COLLMEX_INI", os.environ.get("COLLMEX_INI"))
    os.environ["COLLMEX_INI"] = path


@pytest.fixture(scope="session")
def faux_collmex():
    """Runs tests against a faux Collmex server (see this module).

    Starts a faux server on a local port for the whole test session and
    points the ``COLLMEX_API_URL`` environment variable at it; if no
    ``collmex.ini`` can be found, a temporary one with dummy credentials
    is provided. When the session ends, the server is stopped and the
    environment is restored.

    Yields the server object: its ``url`` attribute is the server URL,
    its ``application`` attribute the ``FauxCollmex`` WSGI application
    (whose ``store`` holds the data, and whose ``reset()`` wipes it).

    The fixture is a no-op (yields ``None``) when ``COLLMEX_TEST_LIVE``
    is set (tests shall run against the live system), when
    ``COLLMEX_API_URL`` is already set, or when ``COLLMEX_FAUX=0``
    explicitly disables this behaviour.
    """
    if (
        os.environ.get("COLLMEX_TEST_LIVE")
        or os.environ.get("COLLMEX_FAUX") == "0"
        or os.environ.get("COLLMEX_API_URL")
    ):
        yield None
        return
    saved_env = {
        name: os.environ.get(name)
        for name in ("COLLMEX_API_URL", "COLLMEX_INI")
    }
    _ensure_ini_file(saved_env)
    server = start_server()
    os.environ["COLLMEX_API_URL"] = server.url
    try:
        yield server
    finally:
        stop_server(server)
        for name, value in saved_env.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
