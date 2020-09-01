import time
import argparse

# import asyncio
# from functools import wraps
from jinja2 import Environment, FileSystemLoader
from super_item import SuperItem
import helper_functions as helper
from arcgis import gis

# need to check for no features
# def async_process_item(f):
#     @wraps(f)
#     async def wrapped(*args, **kwargs):
#         return f(*args, **kwargs)
#     return wrapped

# @async_process_item


def process_item(index, item):
    print(f"I've just started working on item {index} with itemid {item.itemid}")

    super_item = SuperItem(item)
    # a = super_item.get_constructed_obj()
    if super_item.constructed_obj is not None:  # if the object was able to be created
        super_item = helper.run_tests(super_item)  # run the tests for this

    if super_item.problems:
        return super_item

    for layer in super_item.layers:
        if len(layer.problems) > 0:
            return super_item

    else:
        return False


# def process_org_async(items):
#     loop = asyncio.get_event_loop()
#     tasks = [loop.create_task(process_item(index, item)) for index, item in enumerate(items)]

#     try:
#         super_items = loop.run_until_complete(asyncio.gather(*tasks))

#     finally:
#         loop.close()

# serialize_org_report(super_items)


def process_org_sequentially(items):
    super_items = []
    for index, item in enumerate(items):
        super_item = process_item(index, item)
        if super_item:
            super_items.append(super_item)

    serialize_org_report(super_items)


def serialize_org_report(super_items):
    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    template = env.get_template("template.txt")
    output = template.render(super_items=super_items, gis=SuperItem.GIS_OBJ)

    with open("org_clean_up.html", "w") as writer_obj:
        writer_obj.write(output)


def get_items_from_folders(
    gis_obj, folders: list, item_types=None
) -> list:  # folder=None returns the root folder
    all_items = []
    for folder in folders:
        folder_items = gis_obj.users.me.items(folder=folder)
        all_items.extend(folder_items)

    if item_types:
        filtered_items = [item for item in all_items if item.type in item_types]
        return filtered_items

    return all_items


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-target_org",
        dest="target_org",
        help="The organization to tag items in",
        required=True,
    )
    parser.add_argument("-username", dest="username", help="username", required=True)
    parser.add_argument("-password", dest="password", help="pass", required=True)
    args = parser.parse_args()

    # os.chdir('~/Documents/org_clean_up')
    SUPER_ITEM = SuperItem
    SUPER_ITEM.GIS_OBJ = gis.GIS(
        url=args.target_org,
        username=args.username,
        password=args.password,
        verify_cert=False,
    )
    USERNAME = SUPER_ITEM.GIS_OBJ.users.me.username
    # ITEMS = SUPER_ITEM.GIS_OBJ.content.search(f"type:('Feature Service' OR 'Map Service')\
    # owner:{USERNAME}", max_items=10, outside_org=False)
    # ITEMS = SUPER_ITEM.GIS_OBJ.content.search(f"type:'Web Map' owner:{USERNAME}", max_items=20, outside_org=False)
    ITEMS = SUPER_ITEM.GIS_OBJ.content.advanced_search(
        f"type:('Feature Service' OR 'Map Service') OR type:'Web Map' OR type:Dashboard owner:{USERNAME}",
        max_items=2_000,
    )["results"]
    print(f"I found {len(ITEMS)} items")
    # ITEMS = [SUPER_ITEM.GIS_OBJ.content.get(itemid='')]
    # ITEMS = helper.get_items_from_folder(gis=SUPER_ITEM.GIS_OBJ, folder="Broken_Old_Depreciated_Data")
    # ITEMS = SUPER_ITEM.GIS_OBJ.content.search(f"type:Dashboard owner:"USERNAME"", max_items=1000, outside_org=False)

    for ITEM in ITEMS:
        if ITEM.type not in SuperItem.known_item_types:
            print(ITEM.type)

    FILTERED_ITEMS = [ITEM for ITEM in ITEMS if ITEM.type in SUPER_ITEM.supported_items]
    IGNORED_ITEM_IDS = [
        ITEM.id
        for ITEM in get_items_from_folders(
            gis=SUPER_ITEM.GIS_OBJ,
            folders=[
                "_Trash_Can",
                "Error_Route",
                "Secured_Services",
                "Vector_Tile_Layers",
                "Basemaps",
            ],
        )
    ]
    IGNORED_ITEM_IDS + [
        "99170654fe3e4bc7be95771de76b6a2a",
        "6f56ece8eef7473a9bbab065c14ec58b",
        "4bb1f590f3ca48baa5ab1205ab6e629f",
    ]
    SUPER_FILTERED_ITEMS = [
        ITEM for ITEM in FILTERED_ITEMS if ITEM.id not in IGNORED_ITEM_IDS
    ]
    print(f"I'm going to work on {len(FILTERED_ITEMS)} items")
    START_TIME = time.time()
    process_org_sequentially(FILTERED_ITEMS)
    print(f"I took {(time.time() - START_TIME)/60} minutes to complete")
