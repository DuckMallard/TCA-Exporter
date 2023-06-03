[![Win/Mac/Linux](https://img.shields.io/badge/platform-windows%20%7C%20macos%20%7C%20linux-informational)]()
## TCA-Exporter
A Blender addon to convert models in blender into a format that can be loaded into the game Tiny Combat Arena.

Copyright (c) 2023 JMayh with [MIT License](https://github.com/DuckMallard/TCA-Exporter/blob/master/LICENSE.txt)

Credit to [Why485](https://twitter.com/Why485) and [Microprose](https://www.microprose.com/games/tiny-combat-arena/) for Tiny Combat Arena
___
### How does this work?
- Anyone can make a model in Blender of their favourite aircraft, vehicle, or munition they want to see in TCA.
- They can use this addon to create an [assetbundle](https://docs.unity3d.com/Manual/AssetBundlesIntro.html) which contains all of the models data.
- Assetbundles allow you to easily send your TCA models as a single file to anyone on any platform.
- The TCA-Injector Plugin allows you to view the models in game, and reference them in the games JSON files.
___
### Mandatory Prerequisites
- [Blender](https://www.blender.org/download/) (2.80.0) - Blender is a free open source modelling software that is easy to learn and is beginner friendly.
- [Tiny Combat Arena](https://store.steampowered.com/app/1347550/Tiny_Combat_Arena/) (0.11.1.2T) - You will need to have purchased Tiny Combat Arena to use this addon. Additionally this Addon contains no artwork, code or other data from the game.
- [TCA-Injecter Plugin](https://github.com/DuckMallard/TCA-Injector) (0.1.0) - This plugin allows TCA to open assetbundles and make them available in the game. Without this you cannot view exported models in TCA.
- [Bepinex](https://github.com/BepInEx/BepInEx/releases) (5.4.21) **LTS** - Bepinex loads the the previously mentiond plugin. It is easy to install and can be used to run plugins for anyone. One day TCA might come with Bepinex already installed but for now its just a few clicks to setup..
### Optional Software:
- [UABE](https://github.com/SeriousCache/UABE/releases) (3.0B1) - UABE allows more advance modifications to be done, such as referencing existing TCA shaders or using assets for unity's standard library.
___
### Getting Started
- Download Blender if you havent already got it from [here](https://www.blender.org/download/), and ensure you have Tiny Combat Arena downloaded or purchase it [here](https://store.steampowered.com/app/1347550/Tiny_Combat_Arena/).
- Download this repository as a .ZIP file and don't unzip.
- Open Blender, got to Edit > Preferences > Addons then click install. In the popup window location the .ZIP file and install it, you may have to disable some filters in the file browser.
- Ensure the Addon is enabled in the addon browser, if not tick the box that enables it.
- Now when you go to File > Export > TCA Export a popup will appear allowing you to select the location for your extracted models to be saved.
- It's reccomend to save them in the folder TinyCombatArena/AssetBundles, if that folder doesn't exist quickly create it then carry on.
- Now have a look at how to get the Injector Plugin installed so you can view your models in TCA
___
### Notes:
- This is a very early release and has many bugs. Either open an issue, or hop on the [TCA Modding Server](https://discord.gg/D5ScNgcTJh) to recieve support.
- This Addon is also in its infancy and cannot support some more complex modding. At the moment custom textures arent supported. This is the next area of development and should hopefully be functioning soon.
