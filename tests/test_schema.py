from mgs.metadata import EntityType, NavigationProperty, Property
from mgs.schema import schema_from


def test_schema_from_lists_properties_navigations_operations():
    et = EntityType(
        name="message",
        namespace="microsoft.graph",
        properties=[Property("subject", "Edm.String", True)],
        navigations=[
            NavigationProperty("attachments", "Collection(microsoft.graph.attachment)", True)
        ],
    )
    ops = [{"name": "reply", "parameters": [["comment", "Edm.String"]]}]
    v = schema_from(et, ops)
    assert v["entityType"] == "message"
    assert v["properties"][0]["name"] == "subject"
    assert v["navigations"][0]["collection"] is True
    assert v["operations"][0]["name"] == "reply"
    assert v["operations"][0]["parameters"][0] == {"name": "comment", "type": "Edm.String"}
