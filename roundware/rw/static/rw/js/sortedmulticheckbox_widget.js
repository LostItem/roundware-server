( function($) {

    // make this a named function so we can call on AJAX POST success
    function rewriteSortedMultiCheckbox() {
        $('.sortedm2m').parents('ul').each(function () {
            $(this).addClass('sortedm2m');
            var checkboxes = $(this).find('input[type=checkbox]');
            var id = checkboxes.first().attr('id').match(/^(.*)_\d+$/)[1];
            var name = checkboxes.first().attr('name');
            checkboxes.removeAttr('name');
            $(this).before('<input type="hidden" id="' + id + '" name="' + name + '" />');
            var that = this;
            var hdn_indexes = $('input#id_ui_group_edit-ui_items_tags_indexes');
            var recalculate_value = function () {
                var values = [];
                var all_vals = [];
                $(that).find(':checked').each(function () {
                    values.push($(this).val());
                });
                $('#' + id).val(values.join(','));
                // update hidden indexes field
                $(that).find('input[type=checkbox]').each( function() {
                    all_vals.push($(this).val());
                })
                hdn_indexes.val(all_vals.join(','));
            }
            recalculate_value();
            checkboxes.change(recalculate_value);
            $(this).sortable({
                axis: 'y',
                //containment: 'parent',
                update: recalculate_value
            });
        });

        $('.sortedm2m-container .selector-filter input').each(function () {
            $(this).bind('input', function() {
                var search = $(this).val().toLowerCase();
                var $el = $(this).closest('.selector-filter');
                var $container = $el.siblings('ul').each(function() {
                    // walk over each child list el and do name comparisons
                    $(this).children().each(function() {
                        var curr = $(this).find('label').text().toLowerCase();
                        if (curr.indexOf(search) === -1) {
                            $(this).css('display', 'none');
                        } else {
                            $(this).css('display', 'inherit');
                        };
                    });
                });
            });
        });

    }
    $(document).ready(function(){ rewriteSortedMultiCheckbox(); });
})(jQuery);
