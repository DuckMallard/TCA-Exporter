cls
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\blends
del M1.blend
copy M1(original).blend M1(copy).blend
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\
blender blends\M1(copy).blend --background -P blend_script.py > output/log.txt
cls
