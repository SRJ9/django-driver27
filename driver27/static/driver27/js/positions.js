$(function () {
    var drivers = [];
    var drivers_lookup = [];

    function dnsEvent() {
        var closest_li = $(this).closest('li');
        if (closest_li.hasClass('is-dns')) {
            closest_li.removeClass('is-dns');
        } else {
            closest_li.addClass('is-dns').find('.position').text('-');
        }
    }

    function order_all_results() {
        $('.ui-sortable').each(function (i, el) {
            order_results(el);
        });
    }

    function deleteEvent() {
        var closest_li = $(this).closest('li');
        closest_li.removeClass('ui-sortable-handle');
        var seat_id = parseInt(closest_li.data('seat'));
        $('.ui-sortable').find('[data-seat=' + seat_id + ']').remove();
        order_all_results();
        $('#other_seats').append(closest_li);
        closest_li.find('.add-button').on('click', addButtonEvent);
    }

    function addButtonEvent() {
        var closest_li = $(this).closest('li').addClass('is-dns');
        var driver = closest_li.data('driver');
        if ($('.ui-sortable [data-driver=' + driver + ']').length > 0) {
            alert('There is at least one seat with this driver. Delete before add.');
        } else {
            $('.ui-sortable').append(closest_li).sortable('refresh');
        }
    }

    function order_results(target) {
        $(target).children().each(function () {
            var text_pos = pos = $(this).index() + 1;
            var is_dns = $(this).hasClass('is-dns');
            if (is_dns) {
                text_pos = '-';
                pos = null;
            }
            $(this).find('.position').text(text_pos);
            var seat_id = parseInt($(this).data('seat'));
            if (!(seat_id in drivers_lookup)) {
                drivers.push({'id': seat_id});

                drivers_lookup[seat_id] = drivers.length - 1;
            }
            var driver_lookup = drivers_lookup[seat_id];
            drivers[driver_lookup][target.id] = pos;
        });

    }

    $(".ordered-race-results").sortable(
        {
            stop: function (event, ui) {
                order_results(event.target);
            }
        }
    ).disableSelection();

    $('.dns-button').on('click', dnsEvent);

    $('.add-button').on('click', addButtonEvent);

    $('.delete-button').on('click', deleteEvent);
});