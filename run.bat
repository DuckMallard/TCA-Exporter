cls
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\blends
del A-4(copy).blend1
copy A-4(original).blend A-4(copy).blend
cd C:\Users\jmayh\Documents\Programming\TCA-FINAL\
blender blends\A-4(copy).blend --background -P blend_script.py > output/log.txt
del blends\A-4(copy).blend
copy output\created_bundle "C:\Program Files (x86)\Steam\Backups\TinyCombatArenaBepinex\AssetBundles\"
