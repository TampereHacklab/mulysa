async function renderTransactionsGraph() {

    const container = document.getElementById('transactionsGraphContainer');
    const graphcanvas = container.querySelector("#transactionsGraph");

    const Groupings = {
        'day': gettext('daily'),
        'week': gettext('weekly'),
        'month': gettext('monthly'),
        'year': gettext('yearly')
    }
    var buttonContainer = document.createElement("div");
    buttonContainer.className = "transactionGraphGroupingContainer";
    buttonContainer.onclick = function (event) {
        event.stopPropagation();
        event.preventDefault();
        var buttons = buttonContainer.querySelectorAll('a.btn');
        buttons.forEach(function(button) {
            button.classList.remove('btn-primary');
            button.classList.add('btn-secondary');
        });
        grouping = event.target.dataset.grouping;
        chart.options.scales.x.time.unit = event.target.dataset.grouping;
        chart.options.scales.x.time.round = event.target.dataset.grouping;
        chart.update();
        event.target.classList.remove('btn-secondary');
        event.target.classList.add('btn-primary');
    };
    container.prepend(buttonContainer);
    Object.entries(Groupings).forEach(([key, value]) => {
        var btn = document.createElement("a");
        btn.className = "btn btn-secondary mr-2 transactionGroupingButton";
        btn.id = "transactionGraphGrouping_" + key;
        btn.dataset.grouping = key;
        btn.innerText = value;
        buttonContainer.append(btn);
    });
    // default to month
    container.querySelector('#transactionGraphGrouping_month').classList.remove('btn-secondary');
    container.querySelector('#transactionGraphGrouping_month').classList.add('btn-primary');

    // for now default to fetching data 1 year back from now
    let startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 1);
    const queryParams = {
        date__gte: startDate.toISOString().slice(0, 10),
    };
    const searchParams = new URLSearchParams(queryParams);
    const response = await fetch("/api/v1/banktransactionaggregate/?" + searchParams.toString());
    const data = await response.json();
    let labels = [];
    let deposits = [];
    let withdrawals = [];
    for (i = 0; i < data.length; i++) {
        labels.push(data[i].aggregatedate);
        deposits.push(data[i].deposits);
        withdrawals.push(data[i].withdrawals);
    }

    // render the chart
    chart = new Chart(graphcanvas, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                {
                    label: gettext('Deposits'),
                    data: deposits,
                    backgroundColor: "#227D7D"
                },
                {
                    label: gettext('Withdrawals'),
                    data: withdrawals,
                    backgroundColor: "#D13838"
                },
            ],
        },
        options: {
            legend: { display: true },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'month',
                        round: 'month'
                    },
                    stacked: true,
                },
            },
        },
    });

}
renderTransactionsGraph();