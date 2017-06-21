require([
    'underscore',
    'jquery',
    'splunkjs/mvc',
    'splunkjs/mvc/simplexml/ready!'
], function(_, $, mvc) {

	console.log(‘This is working’);

});


$(document.body).on('click', '#getButton', function(e) {

    e.preventDefault();

    var service = mvc.createService();
    var get_data = $('#userGETForm').serializeArray();
    var cleaned_data = {};

    cleanData = function(data) {
        _.each(data, function(field) {
            var key = field['name'];
            var value = field['value'];

            cleaned_data[key] = value;
        });
    }

    cleanData(get_data);

    service.get('/services/receive', cleaned_data, function(err, response) {

        if(err) {
            console.log('error: ', err);
        }
        else if(response.status === 200) {
            console.log('Response: ', response.data);
            var response_data = JSON.parse(response.data);
            $('#getResponseBox').empty();
            $('#getResponseBox').append('Roles: ' + response_data.entry[0].content.roles

            $('#userGETForm')[0].reset();
        }

    });

});
