let graphicsData = null;
$(document).ready(function () {
   console.log(JSON.stringify(graphicsData));
   console.log(Date.parse('2019-08-08T12:12:13'));
   console.log(JSON.parse(JSON.stringify(graphicsData), JSON.dateParser));
});

function getDatetime(str){
    console.log(str);
    console.log(typeof str);
    // console.log(str.match(/(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d:{1,2)/));
    if (typeof str === 'object'){
        return str.map(s=>getDatetime(s));
    }
    else if (typeof str === 'string' && str.match()) {
        let parsed = str.match(/(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d:{1,2)/).slice(1).map(i => parseInt(i));
        return new Date(parsed[0], parsed[1] - 1, parsed[2], parsed[3], parsed[4], parsed[5]);
    }
    else {
        return str;
    }
}


function dateParser(value) {
    let reISO = /(\d{4})-(\d{1,2})-(\d{1,2})T(\d{1,2}):(\d{1,2}):(\d{1,2})/;
    // console.log(value);
    // console.log(typeof value);
    // console.log(reISO.exec(value));
    if (typeof value === 'string' && reISO.exec(value)) {
            return new Date(value);
    }
    else {
        try {
            let classID = parseInt(value);
            switch (classID) {
                case 999:
                    return 'yellow';
                case 0:
                    return 'green';
                case 1:
                    return 'red';
                default:
                    return value;
            }
        }
        catch (e) {
            return value;
        }
    }
        return value;
};
function arrayParser(arr) {
    let newArr = [];
    arr.forEach(function (obj, i, array) {
        newArr.push(obj.map(x=>dateParser(x)));
    });
    console.log(newArr);
    return newArr;
}

// Google charts
google.load("visualization", "1", {packages:["timeline"]});
google.setOnLoadCallback(drawChart);
function drawChart() {
    // console.log(graphicsData.total.data);
    let data_keys = Object.keys(graphicsData);
    // console.log(data_keys);
    let eq_auto_data = [];
    let eq_ids = [];
    data_keys.forEach(function (val, ind, arr) {
        let eq_auto = new google.visualization.DataTable();
        eq_auto.addColumn({ type: 'string', id: 'Role' });
        eq_auto.addColumn({ type: 'string', id: 'Name' });
        eq_auto.addColumn({type: 'string', id: 'style', role: 'style'}),
        eq_auto.addColumn({ type: 'date', id: 'Start' });
        eq_auto.addColumn({ type: 'date', id: 'End' });
        console.log('Try add row');
        graphicsData[val].forEach(function (row, i, array) {
            // let row_data =
            eq_auto.addRow(row.map(v=>dateParser(v)));
        });
        console.log(eq_auto);
        eq_auto_data.push(eq_auto);
        eq_ids.push(val);
    });

    let options_auto = {
        // colors: ['green', 'red', 'yellow'],
        timeline: {
            showRowLabels: false,
            showBarLabels: false
        },
        // width: '100%',
        //height: '20',
        // chartArea: { width: '100%', height:'80%'},
        hAxis: {
            format: "HH:mm"
        }
    };

    eq_auto_data.forEach(function (val, i, arr) {
       let chart = new google.visualization.Timeline(document.getElementById(`graph-${eq_ids[i]}`));
       chart.draw(eq_auto_data[i], options_auto);
    });
}

