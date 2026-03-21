import pygame
from settings import *


class AssetLoader:
    """Loads and caches all tile asset images from the assets folder."""
    def __init__(self):
        self.tile_images = {}
        self.meeple_images = {}
        self.load_all_tiles()

    def load_all_tiles(self):
        load_all_tiles(self.tile_images, "tiles", 100)
        load_all_tiles(self.meeple_images, "meeples", 30)

def load_image_safe(relative_path, scale=None, resize=True):
    try:
        img = pygame.image.load(relative_path).convert_alpha()

        if scale:
            # resolution_display = scale[0] / DEFAULT
            img = pygame.transform.scale(img, scale)
        if resize:
            new_scale = resize_assets(img.get_size())
            img = pygame.transform.scale(img, new_scale)
        print(f"Tải ảnh thành công: {relative_path}")
        return img
    except Exception as e:
        print(f"Lỗi tải ảnh: {relative_path} - {e}")
        surf = pygame.Surface((50, 50))
        surf.fill((50, 50, 50))
        return surf
# ---------------------------------------------------------------------------
# asset loader helpers
# ---------------------------------------------------------------------------

# keep a single loader instance in the module so that every tile refers
# to the same cache of images.  "Lazy" construction avoids doing any work
# until the first tile is created (or :class:`AssetLoader` referenced).
_asset_loader = None

def get_asset_loader():
    global _asset_loader
    if _asset_loader is None:
        _asset_loader = AssetLoader()
    return _asset_loader

def get_image(type, assets):
    loader = get_asset_loader()
    if assets == "Tile":
        entry = loader.tile_images.get(type)
    else:
        entry = loader.meeple_images.get(type)
 
    if entry and 'image' in entry:
        return entry['image']

    surf = pygame.Surface((100, 100), pygame.SRCALPHA)
    surf.fill((200, 0, 0))
    return surf

# automatically load any PNGs in assets folder that are not yet defined

def load_all_tiles(dict_images, subfolder='', size = 80):
    assets_dir = ASSETS_DIR
    if subfolder:
        assets_dir = os.path.join(assets_dir, subfolder)
    for filename in os.listdir(assets_dir):
        if not filename.lower().endswith('.png'):
            continue
        key = os.path.splitext(filename)[0]
        if key in dict_images:
            continue
        relpath = os.path.join(assets_dir, filename)
        dict_images[key] = {
            'image': load_image_safe(relpath, scale = (size, size)),
        }
    # print(dict_images)
