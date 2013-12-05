/**
 * Forms specific features
 */
(function($, Utils, VALIDATION_RULES){

    "use strict";

    $(function() {
        // jQuery validate
        $('form.validation').validate(VALIDATION_RULES);

        // Bootstrap select
        $('.selectpicker').selectpicker();

        // Markdown editor
        $('textarea.md').markdown({
            autofocus: false,
            savable: false
        });

        // Publisher card handling
        $('.publisher-card, .publisher-card a').click(function() {
            var $card = $(this).closest('.publisher-card'),
                $input = $card.closest('.form-group').find('input[type="hidden"]'),
                org_id = $card.data('org-id');

            $(this).closest('.card-list').find('.publisher-card').removeClass('active');
            $card.addClass('active');

            $input.val(org_id);

            return false;
        });

        // Form help messages as popover on info sign
        $('.form-help').popover({
            placement: 'top',
            trigger: 'hover',
            html: true
        });

        // Transforme some links into postable forms
        $('a.postable').click(function() {
            var $a = $(this);

            $('<form/>', {method: 'post', action: $a.attr('href')})
                .append($('<input/>', {name: $a.data('field-name'), value: $a.data('field-value')}))
                .append($('<input/>', {name: 'csrfmiddlewaretoken', value: $.cookie('csrftoken')}))
                .submit();

            return false;
        });
    });

}(window.jQuery, window.Utils, window.ETALAB_VALIDATION_RULES));
