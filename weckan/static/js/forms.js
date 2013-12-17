/**
 * Forms specific features
 */
(function($, Utils, Config){

    "use strict";

    $(function() {
        // jQuery validate
        $('form.validation').validate(Config.rules);

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

        // Formats fields
        $('.format-completer').typeahead({
            name: 'formats',
            prefetch: '/format/autocomplete'
        });

        // Tags
        $('.tag-completer').each(function() {
            $(this).typeahead({
                name: 'tags',
                prefetch: '/tags/autocomplete'
            })
            .tagsManager({
                tagsContainer: $(this).closest('div').find('.tag-container'),
                prefilled: $(this).val(),
                replace: true,
            })
            .on('typeahead:selected', function (e, data) {
                $(this).tagsManager("pushTag", data.main_postal_distribution);
            })
        });

        // Territory fields
        $('.territory-completer').each(function() {
            $(this).typeahead(Config.typeahead.territories)
            .tagsManager({
                tagsContainer: $(this).closest('div').find('.tag-container'),
                prefilled: $(this).val(),
                replace: true,
            })
            .on('typeahead:selected', function (e, data) {
                $(this).tagsManager("pushTag", data.main_postal_distribution);
            })
        });
    });

}(window.jQuery, window.Utils, window.EtalabConfig));
