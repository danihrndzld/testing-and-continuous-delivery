import pytest

from envios import costo_envio

CASOS = [
    pytest.param(-1, None, id="EP-01-negativo"),
    pytest.param(3, 35.0, id="EP-02-tramo-base"),
    pytest.param(12, 77.0, id="EP-03-tramo-adicional"),
    pytest.param(40, None, id="EP-04-mayor-30"),
    pytest.param(4.9, 35.0, id="BVA-01-peso-4.9"),
    pytest.param(5, 35.0, id="BVA-02-peso-5"),
    pytest.param(5.1, 41.0, id="BVA-03-peso-5.1"),
    pytest.param(30, 185.0, id="BVA-04-peso-30"),
]


@pytest.mark.parametrize("peso, esperado", CASOS)
def test_costo_por_peso(peso, esperado):
    if esperado is None:
        with pytest.raises(ValueError):
            costo_envio(peso)
    else:
        assert costo_envio(peso) == esperado


def test_dt_r1_express_duplica():
    assert costo_envio(3, express=True) == 70.0
