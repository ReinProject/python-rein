import gettext
import locale
import logging
import os
import rein.locale

def init_localization():
  '''prepare l10n'''
  locale.setlocale(locale.LC_ALL, '') # use user's preferred locale
  # take first two characters of country code
  loc = locale.getlocale()
  file_name = "messages-%s.mo" % locale.getlocale()[0][0:2]
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
