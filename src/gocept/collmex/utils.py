# copied from http://code.activestate.com/recipes/146306/

from __future__ import unicode_literals
from six.moves import configparser
import mimetypes
import os
import six


def encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.

    files is a sequence of (name, filename, value) elements for data to be
    uploaded as files

    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"'
                 % (key, filename))
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body


def get_content_type(filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def get_collmex_credentials():
    # for testing purposes set 'collmex_credential_section' to
    # 'test-credentials' before initialization of the Collmex object
    section_name = os.environ.get('collmex_credential_section',
                                  'credentials')
    options = ['customer_id', 'company_id', 'username', 'password']

    ini_file = os.environ.get(
        'COLLMEX_INI', _find_ini_file_from_current_directory())
    if not ini_file:
        raise IOError(
            'Could not find a \'collmex.ini\' file in %s'
            ' or any parent directory' % os.getcwd())

    error_message = ('Config file {filename} did not contain a section'
                     ' \'[{section_name}]\' with the following '
                     'options: {options}.'.format(filename=ini_file,
                                                  section_name=section_name,
                                                  options=', '.join(options)))

    config_parser = configparser.ConfigParser()
    with open(ini_file) as f:
        if six.PY3:
            config_parser.read_file(f)
        else:
            config_parser.readfp(f)

    if not config_parser.has_section(section_name):
        # ini file found, but has no credential section
        raise IOError(error_message)

    credentials = dict(config_parser.items(section_name))
    if not all([option in credentials for option in options]):
        # ini file with section found, but not all options were set
        raise IOError(error_message)

    return convert_dict_content_to_unicode(credentials)


def _find_ini_file_from_current_directory():
    ini_file_name = 'collmex.ini'
    current_path = os.getcwd()
    while True:
        ini_file = os.path.join(current_path, ini_file_name)
        if os.path.isfile(ini_file):
            return ini_file

        # if path remains the same we reached the root directory
        if current_path == os.path.dirname(current_path):
            # reached root and did not find an ini file
            return None
        # continue while-loop with parent directory
        current_path = os.path.dirname(current_path)


def convert_dict_content_to_unicode(dictionary):
    new_dictionary = {}
    for key, value in dictionary.items():
        if isinstance(key, six.binary_type):
            key = six.u(key)
        if isinstance(value, six.binary_type):
            value = six.u(value)
        new_dictionary[key] = value
    return new_dictionary
