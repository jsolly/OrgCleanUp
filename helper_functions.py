from GitHub.OrgCleanUp.super_item import SuperItem
from arcgis import features


def strip_error(error):  # Error objects can have nasty carrots which mess up the html
    return str(error).strip("<>")


def get_items_from_folder(
    gis, folder, item_types=None
) -> list:  # folder=None returns the root folder
    items = gis.users.me.items(folder=folder)

    if item_types:
        items = [item for item in items if item.type in item_types]

    return items


def process_super_scene_service_missing_root_node(super_item):  # needs work
    if "store" in super_item.constructed_obj.properties.keys():
        super_item.problems.append(
            "This scene service appears to be missing a root node. It will not be usable in ArcGIS Online or Runtime."
        )
    return super_item


def process_super_webmap_item(webmap_item_):
    webmap_item_ = check_super_webmap_version(webmap_item_)

    # Concatanate all operational layers and basemap layers to a single list
    all_layers = list(webmap_item_.constructed_obj.layers)
    # if 'baseMapLayers' in webmap_item_.webmap_obj.basemap:
    #     all_layers += webmap_item_.webmap_obj.basemap['baseMapLayers']

    if all_layers:
        for layer in all_layers:
            if "url" not in layer:
                continue  # ClientSide Layers
            super_layer = SuperItem(layer)
            if super_layer.constructed_obj:
                super_layer = process_super_layer(super_layer)

            webmap_item_.layers.append(super_layer)

    if webmap_item_.constructed_obj.tables:
        for table in webmap_item_.constructed_obj.tables:
            table_obj = features.Table(url=table["url"], gis=SuperItem.GIS_OBJ)
            super_table = SuperItem(table_obj)
            if super_table.constructed_obj:
                super_table = process_super_layer(super_table)

            webmap_item_.layers.append(super_table)

    if len(webmap_item_.layers) == 0:
        webmap_item_.problems.append(
            f"This webmap has no layers! What a shameful excuse of a map"
        )

    return webmap_item_


def process_super_webscene_item(super_webscene_item):  # needs work
    """
    Take an item, load the scene, then test URLs
    """
    scene = super_webscene_item.constructed_obj
    all_layers = list(scene["operationalLayers"])

    # #basemap layers
    if "baseMap" in scene:
        if "baseMapLayers" in scene["baseMap"]:
            all_layers += scene["baseMap"]["baseMapLayers"]

    # elevation/terrain
    if "ground" in scene:
        if "layers" in scene["ground"]:
            all_layers += scene["ground"]["layers"]

    for layer in all_layers:  # Multiprocessing?
        if "url" not in layer:
            continue  # ClientSide Layers
        super_webscene_layer = SuperItem(layer)
        if super_webscene_layer.problems:
            super_webscene_item.layers.append(super_webscene_layer)

    return super_webscene_item


def process_super_dashboard_item(super_dashboard_item):
    super_dashboard_item = check_super_dashboard_is_old(super_dashboard_item)
    return super_dashboard_item


def process_super_layer(super_layer):
    super_layer_copy = super_layer
    constructed_layer = super_layer_copy.constructed_obj

    super_layer_tests = [
        check_super_feature_layer_for_http,
        check_super_feature_layer_for_production_resources,
        check_super_feature_layer_version,
        check_super_feature_layer_has_no_features,
    ]
    if super_layer_copy.constructed_obj.url[-1].isdigit():
        for super_layer_test in super_layer_tests:
            super_layer_copy = super_layer_test(super_layer_copy)
        return super_layer_copy

    for super_layer_test in super_layer_tests[:-1]:
        super_layer_copy = super_layer_test(super_layer_copy)

    for super_sublayer in constructed_layer.layers:
        super_sublayer = SuperItem(super_sublayer)
        super_layer_copy.layers.append(super_sublayer)

    return super_layer_copy


def check_super_dashboard_is_old(super_dashboard_item):
    dashboard_json = super_dashboard_item.constructed_obj
    if dashboard_json["version"] < 24:
        super_dashboard_item.problems.append("This Dashboard version predates 1.0!")

    elif dashboard_json["version"] == 40:
        super_dashboard_item.problems.append(
            "This Dashboard version is a middleware beta!"
        )

    return super_dashboard_item


def check_super_feature_layer_for_http(super_layer):
    if "https" not in super_layer.constructed_obj.url:
        super_layer.problems.append("feature layer is http")

    return super_layer


def check_super_feature_layer_version(super_layer):
    constructed_layer = super_layer.constructed_obj
    arcgis_server_version = constructed_layer.properties.currentVersion
    if arcgis_server_version <= 9.3:
        super_layer.problems.append(
            f"feature layer is pretty old. The ArcGIS server version is {arcgis_server_version}"
        )

    return super_layer


def check_super_feature_layer_for_production_resources(super_layer):
    constructed_layer = super_layer.constructed_obj

    if super_layer.SERVICE_RE_PROD.match(constructed_layer.url):
        super_layer.problems.append(
            f"This Feature Layer uses production resources {constructed_layer.url}"
        )

    return super_layer


# def check_public_with_editing_enabled(super_layer):
#     important_keys = ["allowAnonymousToDelete", "allowAnonymousToUpdate"]
#     constructed_layer = super_layer.constructed_obj
#     if hasattr(constructed_layer, "properties"):  # Not sure if I need to do this
#         if "Editing" in constructed_layer.properties.capabilities:
#             super_layer.problems.append(f"This layer allows anonomous editing!!")
#     return super_layer


def check_super_webmap_version(webmap_item_):
    constructed_web_map = webmap_item_.constructed_obj
    webmap_spec = constructed_web_map.definition.version
    if int(webmap_spec[0]) < 2:
        webmap_item_.problems.append(
            f"This webmap is outdated. It's webmap spec is {webmap_spec}"
        )

    return webmap_item_


def check_super_max_record_count(super_layer):
    constructed_layer = super_layer.constructed_obj
    total_features = constructed_layer.query(return_count_only=True)

    if "maxRecordCount" not in constructed_layer.properties:
        super_layer.problems.append(
            "This layer does not advertize its max record count!"
        )
        return super_layer

    if constructed_layer.properties.maxRecordCount < total_features:
        super_layer.problems.append(
            "The max record count is less than the total feature count"
        )

    return super_layer

    # feature_layer.properties.maxRecordCount
    # feature_layer.properties.standardMaxRecordCount
    # print (feature_layer.properties.tileMaxRecordCount


def check_super_feature_layer_has_no_features(
    super_feature_layer,
):  # Did it this way because this is also checking to see if the layer can query
    feature_layer = super_feature_layer.constructed_obj

    try:
        feature_count = feature_layer.query(return_count_only=True)

        if feature_count == 0:
            super_feature_layer.problems.append("This layer has no features!")

    except RuntimeError as e:  # happens when querying is not supported
        super_feature_layer.problems.append(e)

    except Exception as e:
        print(e)
        clean_error = strip_error(e)
        super_feature_layer.problems.append(clean_error)

    return super_feature_layer


def run_tests(super_item):
    obj_test_dict = {
        "Dashboard": process_super_dashboard_item,
        "FeatureLayer": process_super_layer,
        "FeatureLayerCollection": process_super_layer,
        "SceneLayer": process_super_scene_service_missing_root_node,
        "Webmap": process_super_webmap_item,
        "Webscene": process_super_webscene_item,
    }
    return obj_test_dict[super_item.constructed_obj_type](super_item)


if __name__ == "__main__":
    print("I'm running all by myself!")
