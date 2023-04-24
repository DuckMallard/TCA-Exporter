cls
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\blends
del A-4(copy).blend
copy A-4(original).blend A-4(copy).blend
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\
blender blends\A-4(copy).blend --background -P blend_script.py > output/log.txt
cls
