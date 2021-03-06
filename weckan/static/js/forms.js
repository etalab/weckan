/**
 * Forms specific features
 */
(function($, Utils, Config){

    "use strict";

    var sso_url = $('link[rel="sso"]').attr('href'),
        user_template = [
            '<div class="logo">',
            '<img src="{{profile.avatar}}">',
            '</div>',
            '<p>{{fullname}}</p>'
        ].join(''),
        RE_TAG = /^[\w\u00C0-\u017F \-.]*$/;

    $.fn.selectpicker.defaults.noneSelectedText = Utils.i18n('none-selected');
    $.fn.selectpicker.defaults.countSelectedText = Utils.i18n('count-selected');

    $.ajaxSetup({
        crossDomain: true,
        xhrFields: {
            withCredentials: true
        }
    });

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
            container: 'body',
            html: true
        });

        // Transforme some links into postable forms
        $('a.postable').click(function() {
            var $a = $(this);

            $('<form/>', {method: 'post', action: $a.attr('href')})
                .append($('<input/>', {name: $a.data('field-name'), value: $a.data('field-value')}))
                .append($('<input/>', {name: 'csrfmiddlewaretoken', value: $.cookie('csrftoken')}))
                .appendTo('body')
                .submit();

            return false;
        });

        // Formats fields
        $('.format-completer').typeahead({
            name: 'formats',
            remote: '/format/autocomplete?q=%QUERY'
        });

        // Tags
        $('.tag-completer').each(function() {
            var $this = $(this),
                minlength = parseInt($this.data('tag-minlength')),
                maxlength = parseInt($this.data('tag-maxlength'));
            $this.typeahead({
                name: 'tags',
                remote: '/tags/autocomplete?q=%QUERY'
            })
            .tagsManager({
                tagsContainer: $this.closest('div').find('.tag-container'),
                prefilled: $this.val(),
                validator: function (tag) {
                    return (tag.length >= minlength && tag.length <= maxlength && RE_TAG.test(tag));
                }
            })
            .on('typeahead:selected', function (e, data) {
                $this.tagsManager("pushTag", data.main_postal_distribution);
            })
            .closest('form').submit(function() {
                var hidden_name = 'hidden-' + $this.attr('name');
                $this.val($this.siblings('input[name="'+hidden_name+'"]').val());
            });
        });

        // Territory fields
        $('.territory-completer').each(function() {
            var $this = $(this);
            $this.typeahead(Config.typeahead.territories)
            .tagsManager({
                tagsContainer: $this.closest('div').find('.tag-container'),
                prefilled: $this.val(),
                onlyTagList: true
            })
            .on('typeahead:selected', function (e, data) {
                var tag = data.kind + '/' + data.code + '/' + data.main_postal_distribution;
                $this.tagsManager("pushTag", tag);
            })
            .closest('form').submit(function() {
                var hidden_name = 'hidden-' + $this.attr('name');
                $this.val($this.siblings('input[name="'+hidden_name+'"]').val());
            });
        });

        // User autocomplete
        $('.user-completer').each(function() {
            var $this = $(this);
            $this.typeahead({
                name: 'Users',
                limit: 8,
                valueKey: 'fullname',
                engine: Config.typeahead.organizations.engine,
                template: user_template,
                remote: {
                    url: [sso_url, '/api/users/?search=%QUERY'].join('')
                }
            });
        });

    });

}(window.jQuery, window.Utils, window.EtalabConfig));
