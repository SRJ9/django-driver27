var $ = django.jQuery;
$(document).ready(function () {
    $('#id_grand_prix').change(function () {
        var circuit = $(this).find(':selected').data('circuit');
        var id_circuit = $('#id_circuit');
        if (id_circuit.val() === '') {
            id_circuit.val(circuit).change();
        }
    });

    $('.field-grand_prix select').change(function () {
        var circuit = $(this).find(':selected').data('circuit');
        var tr_parent = $(this).closest('tr');
        var id_circuit = $(tr_parent).find('.field-circuit select');
        if (id_circuit.val() === '') {
            id_circuit.val(circuit).change();
        }
    });
});