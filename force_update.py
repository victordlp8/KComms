import obspython as obs
import os

path = ""
interval = 5
source_name = ""
update_type = "Update Text"

# ------------------------------------------------------------


def update_source():
    global path
    global interval
    global source_name
    global update_type

    source = obs.obs_get_source_by_name(source_name)
    if source is not None:
        if os.path.exists(path):
            if update_type == "text":
                with open(path, "r") as f:
                    text = f.read().strip()
                    settings = obs.obs_data_create()
                    obs.obs_data_set_string(settings, "text", text)
                    obs.obs_source_update(source, settings)
                    obs.obs_data_release(settings)

            elif update_type == "image":
                settings = obs.obs_data_create()
                obs.obs_data_set_string(settings, "file", path)
                obs.obs_source_update(source, settings)
                obs.obs_data_release(settings)

            else:
                obs.script_log(obs.LOG_WARNING, "Invalid update type selected.")
        else:
            obs.script_log(
                obs.LOG_WARNING,
                "Error opening '" + path + "' | The file probably doesn't exist.",
            )
            obs.remove_current_callback()

        obs.obs_source_release(source)


def refresh_pressed(props, prop):
    update_source()


# ------------------------------------------------------------


def script_description():
    return "Updates a text or image source to the text or image file given at every specified interval."


def script_update(settings):
    global path
    global interval
    global source_name
    global update_type

    path = obs.obs_data_get_string(settings, "path")
    interval = obs.obs_data_get_int(settings, "interval")
    source_name = obs.obs_data_get_string(settings, "source")
    update_type = obs.obs_data_get_string(settings, "update_type")

    obs.timer_remove(update_source)

    if path and source_name:
        obs.timer_add(update_source, interval)


def script_defaults(settings):
    obs.obs_data_set_default_int(settings, "interval", 5)
    obs.obs_data_set_default_string(settings, "update_type", "text")


def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_text(props, "path", "File Path", obs.OBS_TEXT_DEFAULT)

    p = obs.obs_properties_add_list(
        props,
        "source",
        "Source",
        obs.OBS_COMBO_TYPE_EDITABLE,
        obs.OBS_COMBO_FORMAT_STRING,
    )
    sources = obs.obs_enum_sources()
    if sources is not None:
        for source in sources:
            source_id = obs.obs_source_get_unversioned_id(source)
            if (
                source_id == "text_gdiplus"
                or source_id == "text_ft2_source"
                or source_id == "image_source"
            ):
                name = obs.obs_source_get_name(source)
                obs.obs_property_list_add_string(p, name, name)

        obs.source_list_release(sources)

    obs.obs_properties_add_int(props, "interval", "Update Interval (ms)", 5, 3600, 1)

    p = obs.obs_properties_add_list(
        props,
        "update_type",
        "Update",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING,
    )
    obs.obs_property_list_add_string(p, "Image", "image")
    obs.obs_property_list_add_string(p, "Text", "text")

    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
    return props
