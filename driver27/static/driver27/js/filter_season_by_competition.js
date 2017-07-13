$(document).ready(function(){
   $('select[name=competition_selector]').change(function(){
       select_competition(this);
   })
});

function select_competition(selector) {
    var selected = $(selector).find(':selected');
    if (selected) {
        var competition = selected.val();
        if (competition) {
            $('.season-stat').each(function (index, element) {
                if ($(element).data('competition') !== competition) {
                    $(element).addClass("hide");
                } else {
                    $(element).removeClass("hide");
                }
            });
            $('.summary_count').each(function (index, element) {
                var stat = $(element).data('stat');
                $(element).text($(selected).data(stat));
            });
        } else {
            $('.season-stat').removeClass('hide');
            $('.summary_count').each(function (index, element) {
                $(element).text($(element).data('original'));
            })
        }
    }
}
