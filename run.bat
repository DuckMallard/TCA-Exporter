cls
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\blends
del M2(copy).blend
copy M2(original).blend M2(copy).blend
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\
blender blends\M2(copy).blend --background -P blend_script.py > output/log.txt
del M2(copy).blend
cls
