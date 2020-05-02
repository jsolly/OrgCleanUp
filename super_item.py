from json.decoder import JSONDecodeError
from urllib.error import URLError
import signal
from arcgis import gis, features, mapping
import requests

def handler(signum, frame):
    print("I timed out!")
    raise TimeoutError


def strip_error(error): # Error objects can have nasty carrots which mess up the html
    return str(error).strip('<>')
    

class SuperItem:
    GIS_OBJ = None

    supported_items = [
        "Dashboard",
        "Map Service",
        "Web Map",
        "Feature Service",
        "Feature Layer",
        "ArcGISFeatureLayer",
        "ArcGISMapServiceLayer",
        "Feature Collection",
        "Group Layer",
        "Network Dataset Layer",
        "KML",
        "ArcGISTiledMapServiceLayer",
        "Table"
    ]

    unsupported_items = [
        "Web Mapping Application",
        "ArcGISImageServiceLayer",
        "WFS",
        "GeoRSS",
        "WMS",
        "ImageServer",
        "Operation View",
        "Shapefile",
        "CSV Collection",
        "File Geodatabase",
        "Vector Tile Package",
        "Microsoft Excel",
        "Stream Service",
        "Vector Tile Service",
        "Microsoft Word",
        "Service Definition",
        "Code Attachment",
        "WFS",
        "ArcGISStreamLayer",
        "CSV",
        "GeoJson",
        "Operations Dashboard Add In",
        "Operations Dashboard Extension",
        "Document Link",
        "Image",
        "Form",
        "Workforce Project",
        "Scene Service",
        "Web Scene",
        "Raster Layer",
        "Mosaic Layer"
    ]

    known_item_types = unsupported_items + supported_items

    def __init__(self, obj):
        self.item_hierarchy = {}
        self.unconstructed_obj = obj
        self.layers = []
        self.problems = []
        self.constructed_obj = None
        #signal.signal(signal.SIGALRM, handler)
        #signal.alarm(5) # If it takes longer than 5 seconds to get a contructed layer, timeout the layer

        def get_constructed_obj(self):
            object_cook_book_dict = {
                "Web Map": get_constructed_web_map,
                "Web Scene": get_constructed_web_scene,
                "Feature Service": get_constructed_feature_layer_from_item,
                "Map Service": get_constructed_feature_layer_from_item,
                "Feature Collection": get_constructed_feature_layer_from_item,
                "Webmap Layer": get_constructed_feature_layer_from_webmap_layer,
                "Feature Layer": get_constructed_layer,
                "ArcGISSceneServiceLayer": get_constructed_scene_layer,
                "FeaureLayerCollection": get_constructed_feature_layer_collection,
                "CSV": get_constructed_feature_layer_from_webmap_layer,
                "ArcGISFeatureLayer": get_constructed_feature_layer_from_webmap_layer,
                "ArcGISMapServiceLayer": get_constructed_feature_layer_from_webmap_layer,
                "KML": get_constructed_feature_layer_from_webmap_layer,
                "ArcGISTiledMapServiceLayer": get_constructed_feature_layer_from_webmap_layer,
                "Group Layer": get_constructed_layer,
                "Network Dataset Layer": get_constructed_layer,
                "SceneLayer": get_constructed_scene_layer,
                "Scene Layer": get_constructed_scene_layer,
                "Dashboard": get_constructed_dashboard,
                "Table": get_constructed_table
            }

            try:
                return object_cook_book_dict[self.unconstructed_obj_type](self)

            except AttributeError as e:
                clean_error = strip_error(e)
                self.problems.append(clean_error)

            except RuntimeError as e:
                clean_error = strip_error(e)
                self.problems.append(clean_error)

            except JSONDecodeError as e:
                clean_error = strip_error(e)
                self.problems.append(clean_error)

            except TypeError as e: # Happens when the properties or manager attribute is invalid
                clean_error = strip_error(e)
                self.problems.append(clean_error)

            except URLError as e:
                clean_error = strip_error(e)
                self.problems.append(clean_error)

            except requests.exceptions.ConnectionError as e:
                clean_error = strip_error(e)
                self.problems.append(clean_error)

            except requests.exceptions.ReadTimeout as e:
                clean_error = strip_error(e)
                self.problems.append(clean_error)

            except requests.exceptions.MissingSchema as e:
                clean_error = strip_error(e)
                self.problems.append(clean_error)

            except Exception as e:
                print (e)
                clean_error = strip_error(e)
                self.problems.append(clean_error)

        def get_constructed_feature_layer_from_webmap_layer(self):
            webmap_layer = self.unconstructed_obj
            webmap_layer_url = webmap_layer['url']
            requests.get(webmap_layer_url, timeout=10) # make sure url works

            if bool(webmap_layer_url[-1].isdigit()):
                feature_layer_obj = features.FeatureLayer(gis=self.GIS_OBJ, url=webmap_layer_url)
                feature_layer_obj.properties # sometimes this triggers an error
                return ("FeatureLayer", feature_layer_obj)

            feature_layer_collection_obj = features.FeatureLayerCollection(gis=self.GIS_OBJ, url=webmap_layer_url)
            return ("FeatureLayerCollection", feature_layer_collection_obj)

        def get_constructed_feature_layer_from_item(self):
            item = self.unconstructed_obj
            requests.get(item.url, timeout=5) # make sure url works

            if bool(item.url[-1].isdigit()):
                layer = features.FeatureLayer(gis=self.GIS_OBJ, url=item.url)
                layer.properties # sometimes this triggers an error
                return ("FeatureLayer", layer)

            feature_layer_collection = features.FeatureLayerCollection(gis=self.GIS_OBJ, url=item.url)
            return ("FeatureLayerCollection", feature_layer_collection)

        def get_constructed_web_map(self):
            webmap_item = self.unconstructed_obj
            webmap_obj = mapping.WebMap(webmap_item)
            if not isinstance(webmap_obj, mapping._types.WebMap):
                self.problems.append("This Webmap could not be created!")

            return ("Webmap", webmap_obj)

        def get_constructed_dashboard(self):
            dashboard_item = self.unconstructed_obj
            dashboard_json = dashboard_item.get_data()
            if not dashboard_json:
                self.problems.append("This Dasboard is empty")
                dashboard_json = None
            
            elif dashboard_json == {'_ssl': False}: # happens on item 5c40b5f351a14f62a4afbb620575b6b6
                self.problems.append("item.get_data returned {'_ssl': False}")
                dashboard_json = None

            return ("Dashboard", dashboard_json)

        def get_constructed_web_scene(self):
            webscene_item = self.unconstructed_obj
            web_scene_obj = mapping.WebScene(webscene_item)
            return ("Web Scene", web_scene_obj)

        def get_constructed_layer(self):
            layer = self.unconstructed_obj
            requests.get(layer.url, timeout=5) # make sure url works
            return ("FeatureLayer", layer)

        def get_constructed_table(self):
            table = self.unconstructed_obj
            requests.get(table.url, timeout=5)
            return ("Table", table)

        def get_constructed_feature_layer_collection(self):
            feature_layer_collection = self.unconstructed_obj
            requests.get(feature_layer_collection.url, timeout=5) # make sure url works
            return ("FeatureLayerCollection", feature_layer_collection)

        def get_constructed_scene_layer(self):
            scene_layer = self.unconstructed_obj
            requests.get(scene_layer.url, timeout=5) # make sure url works
            scene_layer_obj = mapping.SceneLayer(scene_layer)
            return ("SceneLayer", scene_layer_obj)

        def get_unconstructed_obj_type(self): # I know this sucks, but I don't know any other way
            unconstructed_obj = self.unconstructed_obj

            try:
                if isinstance(unconstructed_obj, gis.Item):
                    return unconstructed_obj.type

                if isinstance(unconstructed_obj, features.layer.FeatureLayer):
                    return unconstructed_obj.properties.type

                elif "type" in unconstructed_obj:
                    return unconstructed_obj.type

                elif "properties" in unconstructed_obj:
                    if "type" in unconstructed_obj.properties:
                        return unconstructed_obj.properties.type

                elif "layerType" in unconstructed_obj:
                    return unconstructed_obj.layerType
                    
                else:
                    split_url = unconstructed_obj.url.split("/")
                    if "MapServer" in split_url or "FeatureServer" in split_url:
                        return "ArcGISFeatureLayer"

                    elif "ImageServer" in split_url:
                        return "ImageServer"

                print("I have no idea what type of item this is")
            except Exception as e: # THIS IS A VERY BROAD EXCEPTION. BEWARE!
                clean_error = strip_error(e)
                self.problems.append(clean_error)

        self.unconstructed_obj_type = get_unconstructed_obj_type(self)

        if self.unconstructed_obj_type not in SuperItem.known_item_types:
            print(f"Unknown item! {self.unconstructed_obj_type}")

        elif self.unconstructed_obj_type in SuperItem.unsupported_items:
            print (f"unsupported layer type, {self.unconstructed_obj_type}")
            self.constructed_obj_type, self.constructed_obj = (None, None)
            
        else:
            #signal.signal(signal.SIGALRM, handler)
            #signal.alarm(5) # If it takes longer than 5 seconds to get a contructed layer, timeout the layer
            try:
                self.constructed_obj_type, self.constructed_obj = get_constructed_obj(self)
            except TypeError:
                self.constructed_obj_type, self.constructed_obj = (None, None)