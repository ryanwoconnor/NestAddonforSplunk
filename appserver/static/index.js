require.config({
    paths: {
        text: "../app/NestAddonforSplunk/components/lib/text",
        'nestConfigTemplate' : '../app/NestAddonforSplunk/components/templates/index.html'
    }
});

require([
    "underscore",
    "backbone",
    "splunkjs/mvc",
    "jquery",
    "splunkjs/mvc/simplesplunkview",
    '../app/NestAddonforSplunk/components/views/settingsView',
    "text!nestConfigTemplate",
], function( _, Backbone, mvc, $, SimpleSplunkView, SettingsView, NestConfigTemplate){

    var NestConfigView = SimpleSplunkView.extend({

        className: "NestConfigView",

        el: '#nestConfigWrapper',

        initialize: function() {
            this.options = _.extend({}, this.options);
            this.render();
        },

        _loadSettings: function() {

            var that = this;
            var configComponents = $('#nestConfig-template', this.$el).text();
            $("#content", this.$el).html(_.template(configComponents));

            new SettingsView({
                id: "settingsView",
                el: $('#nestComponentsWrapper')
            }).render();
        },

        render: function() {

            document.title = "Nest Addon for Splunk Setup";

            var that = this;
            $(this.$el).html(_.template(NestConfigTemplate));

            this._loadSettings();

            return this;
        }

    });

    new NestConfigView();

});