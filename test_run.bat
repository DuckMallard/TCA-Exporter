cls
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\blends
del Test(copy).blend
copy Test(original).blend Test(copy).blend
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\
blender blends\Test(copy).blend --background -P blend_script.py > output/log.txt
cls
