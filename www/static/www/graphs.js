async function renderTransactionsGraph() {
    // for now default to fetching 1 year back
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
    chart = new Chart(document.getElementById("transactions"), {
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

/**
 * Change transaction graph grouping
 *
 * @param {string} value - Change grouping. Accepted values 'day', 'week', 'month', 'year'. Defaults to day.
 */
function changeTransactionGraphGrouping(value = 'day') {
    const chart = Chart.getChart("transactions");
    chart.options.scales.x.time.unit = value;
    chart.options.scales.x.time.round = value;
    chart.update();
    return true;
}