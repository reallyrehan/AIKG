$(function() {
    $.ajax({
        url: '/api/info',
        success: function(data) {
            console.log('get info');
            $('#info').html(JSON.stringify(data, null, '   '));
            $('#description').html(data['description']);
        }
    });
 
    $('#calc').click(function() {
        //console.log(url);
        $.ajax({
            url : '/api/calc?a=' + document.getElementById('a').value + '&b=' + document.getElementById('b').value + '&query=' +document.getElementById('query_input').value,
            success: function(data) {
                $('#add').html(data['a'] + ' + ' + data['b'] + ' = ' + data['add']);
                $('#subtract').html(data['a'] + ' - ' + data['b'] + ' = ' + data['subtract']);
                $('#multiply').html(data['a'] + ' * ' + data['b'] + ' = ' + data['multiply']);
                $('#divide').html(data['a'] + ' / ' + data['b'] + ' = ' + data['divide']);
            }
        });
    });
})