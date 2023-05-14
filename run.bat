cls
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\blends
del Mig23MLA(copy).blend
copy Mig23MLA(original).blend Mig23MLA(copy).blend
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\
blender blends\Mig23MLA(copy).blend --background -P blend_script.py > output/log.txt
cls
