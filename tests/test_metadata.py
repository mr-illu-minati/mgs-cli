from mgs.metadata import EntityType, Metadata, NavigationProperty, Operation, Property


def _sample():
    return Metadata(
        entity_types=[
            EntityType(
                name="user",
                namespace="microsoft.graph.security",
                properties=[Property("id", "Edm.String", True)],
                navigations=[],
            ),
            EntityType(
                name="user",
                namespace="microsoft.graph",
                properties=[Property("displayName", "Edm.String", True)],
                navigations=[NavigationProperty("messages", "Collection(microsoft.graph.message)", True)],
            ),
        ],
        actions=[Operation("sendMail", bound_to="user", parameters=[])],
        functions=[],
    )


def test_entity_type_prefers_microsoft_graph_namespace():
    md = _sample()
    user = md.entity_type("user")
    assert user is not None
    assert user.namespace == "microsoft.graph"
    assert user.properties[0].name == "displayName"


def test_entity_type_unknown_is_none():
    assert _sample().entity_type("nope") is None


def test_operations_bound_to():
    ops = list(_sample().operations_bound_to("user"))
    assert [o.name for o in ops] == ["sendMail"]
