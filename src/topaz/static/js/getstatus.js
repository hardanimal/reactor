var timerId;
var statusList
var TIME_REFRESH = 1000 // ms
var STATUS = {
        "1" : "IDEL",
        "2" : "BLANK",
        "3" : "Testing",
        "4" : "PASS",
        "5" : "FAIL",
    }

$(document).ready(function() {

    var i = 1
    for (var z = 1; z <= 2; z++) {
        $("#channels").append(
                '<div id="channel' + z
                        + '" class="col-md-6"></div>')
        $('#channel' + z)
                .append(
                        '<div class="row" align="center">CHANNEL '
                                + z
                                + '</div><hr /><div class="row"><ul id="channel_ul'
                                + z
                                + '" class="bs-glyphicons"></ul></div>')
        for (var x = 0; x < 64; x++) {
            $('#channel_ul' + z)
                    .append(
                            '<li class="dut_cell active lightview" href="#chartscontainer">'
                                + '<span class="glyphicon-class">'
                                    + i
                                + '</span>'
                                + '<div class="progress">'
                                    + '<div id="'+ i + '"class="progress-bar dut_label" style="width: 100%">'
                                +   '</div>' 
                                + '</div>'
                            + '</li>')
            i++;
        }
    }

    //
    // build highcharts form option
    //
    options = {
        chart : {
            renderTo : '',
            height : 300
        },
        title : {
            text : '',
            x : -20
        // center
        },
        subtitle : {
            text : '',
            x : -20
        },
        xAxis:{
            tickInterval: 1,
            categories : []
        },
        yAxis : {
            title : {
                text : ''
            },
            plotLines : [ {
                value : 0,
                width : 1,
                color : '#808080'
            } ]
        },
        tooltip : {
        },
        legend : {
            layout : 'vertical',
            align : 'right',
            verticalAlign : 'middle',
            borderWidth : 0
        },
        series : []
    };

    $("#container1", "#container2").empty();
    //
    // table cell click function to bring out line chart
    //
    
    $(".dut_cell").click(function(){
        el = $(this);
        dut_num = parseInt(el.children('span.glyphicon-class').text())
        dut = statusList[dut_num-1]
        cyc_len = dut.CYCLES.length
        time = dut.CYCLES[cyc_len-1].TIME
        for(i in time){
            time[i] = time[i].toFixed(2)
        }
        options.xAxis.categories = time
        //
        //  Construct VCAP chart
        //
        optionsV = options
        optionsV.chart.renderTo = "container1"
        optionsV.title.text = 'Current VCAP of DUT'+ dut._id
        optionsV.subtitle.text = "CYCLE: "+ dut.PWRCYCS
        optionsV.yAxis.title.text = "VCAP"
        optionsV.tooltip ={formatter: function() {
            return '<b>'+ this.series.name +'</b><br/>'+
                    this.x +': '+ this.y +' V';
                }
            }
        vcap = dut.CYCLES[cyc_len-1].VCAP
        seriesV = {
                name : "CYCLE: "+ dut.PWRCYCS,
                data : vcap
            }
//      $.each(time, function(itemNo, item) {
//          seriesV.data.push([time[itemNo].toFixed(2),vcap[itemNo]])
//      });
        displaychart = new Highcharts.Chart(optionsV);
        displaychart.addSeries(seriesV);

//      displaychart.redraw();
        //
        //  Construct TEMP chart
        //
        optionsT = options
        optionsT.chart.renderTo = "container2"
        optionsT.yAxis.title.text = "TEMP"
        optionsT.title.text = 'Current VCAP of DUT'+ dut._id
        optionsT.subtitle.text = "CYCLE: "+ dut.PWRCYCS
        optionsT.tooltip ={formatter: function() {
            return '<b>'+ this.series.name +'</b><br/>'+
                    this.x +': '+ this.y +' °C';
                }
            }
        temp = dut.CYCLES[cyc_len-1].TEMP
        seriesT = {
            name : "CYCLE: "+ dut.PWRCYCS,
            data : temp
        }
//      $.each(time, function(itemNo, item) {
//          seriesT.data.push([time[itemNo].toFixed(2),temp[itemNo]])
//      });
        displaychart = new Highcharts.Chart(optionsT);
        displaychart.addSeries(seriesT);
        //
        //  Redraw
        //
        displaychart.redraw();
        
//      $.ajax({
//          url : "/getstatus",
//          data : {
//              name : series1.name,
//          },
//          dataType : "json",
//          success : function(response) {
//              cyc_len = response.CYCLES.length
//              options.title.text = 'Current VCAP of DUT'+ response._id
//              options.subtitle.text = "CYCLE: "+ response.PWRCYCS
//              time = response.CYCLES[cyc_len-1].TIME
//              vcap = response.CYCLES[cyc_len-1].VCAP
//              $.each(time, function(itemNo, item) {
//                  series1.data.push([time[itemNo].toFixed(2),vcap[itemNo]])
//              });
//              displaychart = new Highcharts.Chart(options);
//              displaychart.addSeries(series1);
//              displaychart.redraw();
//          },
//          error : function(jqXHR, textStatus, errorThrown) {
//              console.log(textStatus)
//          }
//      });
    });

    //
    // toggle real-time status of single dut when mouse on
    //

    $("div.dut_label").mouseout(function() {
        var el = $(this)
        el.popover('destroy')
    });

    $("div.dut_label").mouseover(function() {
        var el = $(this)
        info =  "model : " + el.attr("model") + "<br/>"
                + "SN : " + el.attr("sn") + "<br/>"
                + "cycle : " + el.attr("pwrcycs") + "<br/>"
                + "status : " + STATUS[el.attr("status")] +"<br/>"
                + "HWVER : " + el.attr("hwver") + "<br/>"
                + "FWVER : " + el.attr("fwver") + "<br/>"
                + "VCAP : " + el.attr("vcap") + "<br/>"
                + "TEMP : " + el.attr("temp") + "<br/>"
                
        el.popover("destroy")
        if(el.attr("status") in ["1","2","3","4","5"]){
            el.popover({
                title : "DUT: " + el.attr("id"),
                content : info,
                html : true,
                delay : {
                    show : 0,
                    hide : 0,
                }
            }).popover('show');
        }
    });
    
    //
    //  refresh DUTs test status
    //
    $(function() {
        timerId = window.setInterval(refreshStatus, TIME_REFRESH);
    });

    function refreshStatus() {
        $.ajax({
            type : "get",
            url : "/newstatus",
            timeout : 30000,
            dataType : "json",
            success : function(data) {
                statusList = data
                $.each(statusList, function(itemNo, item) {
                    current_cyc = item.CYCLES[item.CYCLES.length-1]
                    vcap = current_cyc.VCAP[current_cyc.VCAP.length-1]
                    temp = current_cyc.VCAP[current_cyc.TEMP.length-1]
                    $('div.dut_label#' + item._id).attr({
                        "model" : item.MODEL,
                        "sn" : item.SN,
                        "status" : item.STATUS,
                        "pwrcycs" :item.PWRCYCS,
                        "hwver" : item.HWVER,
                        "fwver" : item.FWVER,
                        "vcap"  : vcap,
                        "temp"  : temp,
                    })
                })
            },
            error : function() {
                window.clearInterval(timerId);
                alert("Request Error");
            }
        });
        $.each($("div.dut_label"),function() {
            el = $(this)
            status = el.attr("status")
            switch (status) {
            case "1":
                el.parent("div").addClass("progress-striped active");
                el.removeClass("progress-bar-success progress-bar-info progress-bar-warning progress-bar-danger");
                el.css("background-color", "");
                el.addClass("progress-bar-info");
                el.css("width", "100%");
                el.text('passed');
                break;
            case "2":
                el.parent("div").removeClass("progress-striped active");
                el.css("width", "100%");
                el.css("background-color", "grey");
                el.text('blank');
                el.removeClass("progress-bar-success progress-bar-info progress-bar-warning progress-bar-danger");
                break;
            case "3":
                el.parent("div").addClass("progress-striped active");
                el.removeClass("progress-bar-success progress-bar-info progress-bar-warning progress-bar-danger");
                el.css("background-color", "");
                el.addClass("progress-bar-warning");
                el.css("width", "100%");
                el.text('testing');
                break;
            case "4":
                el.parent("div").addClass("progress-striped active");
                el.removeClass("progress-bar-success progress-bar-info progress-bar-warning progress-bar-danger");
                el.css("background-color", "");
                el.addClass("progress-bar-success");
                el.css("width", "100%");
                el.text('passed');
                break;
            case "5":
                el.parent("div").addClass("progress-striped active");
                el.removeClass("progress-bar-success progress-bar-info progress-bar-warning progress-bar-danger");
                el.css("background-color", "");
                el.addClass("progress-bar-danger");
                el.css("width", "100%");
                el.text('failed');
                break;
            }
        });
    }
});
