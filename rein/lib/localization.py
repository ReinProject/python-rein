import gettext
import locale
import logging
import os
import rein.locale

def init_localization():
  '''prepare l10n'''
  # Extract system locale identifier
  loc = locale.getdefaultlocale()[0]
  file_name = "messages-%s.mo" % loc.split('_')[0]
  file_path = os.path.join(os.path.dirname(os.path.abspath(rein.locale.__file__)), file_name)
  print(file_path)

  try:
    logging.debug("Opening message file %s for locale %s", file_name, loc[0])
    trans = gettext.GNUTranslations(open(file_path, "rb" ))

  except IOError:
    logging.debug("Locale not found. Using default messages")
    trans = gettext.NullTranslations()

  trans.install()

if __name__ == '__main__':
  init_localization()
