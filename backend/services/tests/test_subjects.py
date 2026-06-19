from services.email_poller import classify_subject


def test_credito_con_tilde_se_reconoce():
    assert classify_subject('Compra con Tarjeta de Crédito') == 'compra'


def test_credito_sin_tilde_tambien():
    assert classify_subject('compra con tarjeta de credito') == 'compra'


def test_pagos():
    assert classify_subject('Pago de Tarjeta de Crédito Nacional') == 'pago_nacional'
    assert classify_subject('Pago de Tarjeta de Crédito Internacional') == 'pago_internacional'


def test_existentes():
    assert classify_subject('Cargo en Cuenta') == 'debito'
    assert classify_subject('Transferencia a Terceros') == 'transferencia'


def test_no_soportado():
    assert classify_subject('Newsletter mensual') is None


def test_giro_con_tilde():
    assert classify_subject('Giro con Tarjeta de Débito') == 'giro'
