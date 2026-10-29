"""Guard: the internal wrapper _lift_deferred depends on must stay importable.

If ibis renames/removes ibis.common.deferred.deferred, this fails loudly with a
clear signal instead of surfacing as an obscure runtime InputTypeError. See
item 226b / Ibis #11742 retirement note.
"""
def test_ibis_deferred_wrapper_importable_and_callable():
    import ibis
    from ibis.common.deferred import Deferred, deferred

    wrapped = deferred(ibis.literal(5))
    assert isinstance(wrapped, Deferred)
