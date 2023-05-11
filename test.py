import UnityPy
from UnityPy.helpers import TypeTreeHelper
TypeTreeHelper.read_typetree_c = False

env = UnityPy.load(r'base_bundle')
sf = list(env.file.files.values())[1]
print(bytes(sf.view))
print(len(sf.view))
# mesh = [asset for asset in sf.objects.values() if asset.type.name == 'Mesh'][0]
# print(mesh.read_typetree())