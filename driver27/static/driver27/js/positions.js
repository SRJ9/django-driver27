$(function () {
    var positions = [];
    var seats_lookup = [];

    function order_all_results() {
        positions = [];seats_lookup = [];
        $('.ui-sortable').each(function (i, el) {
            order_results(el);
        });
    }

    function dnfEvent() {
        var closest_li = $(this).closest('li');
        if (closest_li.hasClass('is-dnf')) {
            closest_li.removeClass('is-dnf');
            order_all_results();
        } else {
            closest_li.addClass('is-dnf').find('.position').text('-');
        }

    }

    function deleteEvent() {
        var closest_li = $(this).closest('li');
        closest_li.find('.position').text('-');
        closest_li.removeClass('ui-sortable-handle');
        var seat_id = parseInt(closest_li.data('seat'));
        $('.ui-sortable').find('[data-seat=' + seat_id + ']').remove();
        order_all_results();
        $('#other_seats').append(closest_li);
        closest_li.find('.add-button').on('click', addButtonEvent);
    }

    function addButtonEvent() {
        var closest_li = $(this).closest('li').addClass('is-dnf');
        var driver = closest_li.data('driver');
        if ($('.ui-sortable [data-driver=' + driver + ']').length > 0) {
            alert('There is at least one seat with this driver. Delete before add.');
        } else {
            $('.ui-sortable').append(closest_li).sortable('refresh');
            order_all_results();
        }
    }

    function wildcardEvent() {
        var closest_li = $(this).closest('li')
        var wildcard = !(closest_li.data('wildcard'));
        if(wildcard){
            closest_li.addClass('is-wildcard');
        } else {
            closest_li.removeClass('is-wildcard');
        }
        var seat = closest_li.data('seat');
        $('.ui-sortable [data-seat=' + seat + ']').data('wildcard', wildcard);

    }

    function order_results(target) {
        $(target).children().each(function () {
            var text_pos = pos = $(this).index() + 1;
            var is_dnf = $(this).hasClass('is-dnf');
            if (is_dnf) {
                text_pos = '-';
                pos = null;
            }
            $(this).find('.position').text(text_pos);
            var seat_id = parseInt($(this).data('seat'));
            if (!(seat_id in seats_lookup)) {
                positions.push({'seat_id': seat_id});

                seats_lookup[seat_id] = positions.length - 1;
            }
            var seat_lookup = seats_lookup[seat_id];
            positions[seat_lookup][target.id] = pos;
            positions[seat_lookup]['wildcard'] = $(this).data('wildcard');
        });

    }

    $('#form-positions').click(function () {
        positions.forEach(function (el, i) {
            el.retired = (el.finish === null || el.finish < 1);
        });

        positions_JSON = JSON.stringify(positions);



        $('<input>').attr({
            type: 'hidden',
            name: 'positions',
            value: positions_JSON
        }).appendTo($(this));

        $(this).submit();


    });

    $(".ordered-race-results").sortable(
        {
            stop: function (event, ui) {
                order_results(event.target);
            }
        }
    ).disableSelection();

    $('.dnf-button').on('click', dnfEvent);
    $('.add-button').on('click', addButtonEvent);
    $('.delete-button').on('click', deleteEvent);
    $('.wildcard-button').on('click', wildcardEvent);

//    Initializing ordered-race-results list
    order_all_results();
});