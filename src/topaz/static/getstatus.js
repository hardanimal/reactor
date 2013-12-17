$(function () {
    options = {
        chart: {
            renderTo: 'container1',
        },
        title: {
            text: 'Current VCAP of DUT',
            x: -20 //center
        },
        subtitle: {
            text: 'Source: 127',
            x: -20
        },
        yAxis: {
            title: {
                text: 'Temperature (°C)'
            },
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080'
            }]
        },
        tooltip: {
            valueSuffix: '°C'
        },
        legend: {
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'middle',
            borderWidth: 0
        },
        series: []
    };

    $("#container1").empty();

    $("#start").click(function() {
        displaychart = new Highcharts.Chart(options);
        series1 = {name: 'DUT1', data: []}
        $.ajax({
            url: "/getstatus",
            data: {name: series1.name},
            dataType: "json",
            success: function(response){
                $.each(response.data, function(itemNo, item) {
                    series1.data.push(item)
                });
                displaychart.addSeries(series1);
                displaychart.redraw();
            },
            error: function(jqXHR,textStatus,errorThrown){
                console.log(textStatus)  
            }
        });
    });
});
