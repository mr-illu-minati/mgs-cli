import json
import time

from mgs.csdl import load_entity_type, parse_edmx

SAMPLE = """
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="microsoft.graph">
      <EntityType Name="message">
        <Property Name="subject" Type="Edm.String" Nullable="true"/>
        <Property Name="isRead" Type="Edm.Boolean"/>
        <NavigationProperty Name="attachments" Type="Collection(microsoft.graph.attachment)"/>
        <NavigationProperty Name="sender" Type="microsoft.graph.recipient"/>
      </EntityType>
      <Action Name="reply" IsBound="true">
        <Parameter Name="bindingParameter" Type="microsoft.graph.message"/>
        <Parameter Name="comment" Type="Edm.String"/>
      </Action>
    </Schema>
    <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="microsoft.graph.security">
      <EntityType Name="message">
        <Property Name="id" Type="Edm.String"/>
      </EntityType>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>
"""


def test_parse_entity_type_properties_and_navigations():
    md = parse_edmx(SAMPLE)
    msg = md.entity_type("message")
    assert msg.namespace == "microsoft.graph"
    assert [p.name for p in msg.properties] == ["subject", "isRead"]
    assert msg.properties[0].nullable is True
    navs = {n.name: n.collection for n in msg.navigations}
    assert navs == {"attachments": True, "sender": False}


def test_parse_bound_action_drops_binding_parameter():
    md = parse_edmx(SAMPLE)
    ops = list(md.operations_bound_to("message"))
    assert len(ops) == 1
    assert ops[0].name == "reply"
    assert [p.name for p in ops[0].parameters] == ["comment"]


def test_load_entity_type_reads_fresh_cache_without_network(tmp_path):
    # Pre-seed a fresh compact cache so no network/parse happens.
    d = tmp_path / "metadata" / "v1"
    (d / "types").mkdir(parents=True)
    (d / "types" / "message.json").write_text(json.dumps({
        "name": "message", "namespace": "microsoft.graph",
        "properties": [["subject", "Edm.String", True]],
        "navigations": [["attachments", "Collection(microsoft.graph.attachment)", True]],
    }))
    (d / "operations.json").write_text(json.dumps({}))
    (d / ".stamp").write_text(str(time.time()))
    et = load_entity_type(str(tmp_path), "message", beta=False)
    assert et is not None
    assert et.name == "message"
    assert et.properties[0].name == "subject"
    assert et.navigations[0].collection is True
