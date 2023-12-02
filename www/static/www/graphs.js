async function renderTransactionsGraph() {
  // for now default to fetching all of last years data and this year untill today

  // today
  let startDate = new Date();
  // one year back
  startDate.setFullYear(startDate.getFullYear() - 1);
  // january
  startDate.setMonth(0);
  // and from the first day of the month
  startDate.setDate(1);

  const queryParams = {
    date__gte: startDate.toISOString().slice(0, 10),
  };
  const searchParams = new URLSearchParams(queryParams);
  const response = await fetch(
    "/api/v1/banktransactionaggregate/?" + searchParams.toString()
  );

  const data = await response.json();

  // helper for building grouped data by month / year from the daily aggregate data
  // TODO: add back the week grouping :)
  let buildGroupedDataGraphData = function(data, grouping) {
    let labels = new Set();
    let deposits = [];
    let withdrawals = [];

    // default to full date format 2022-01-01
    let l = 10;

    data.forEach(item => {
      if (grouping === "month") {
        l = 7; // 2022-01
      }
      if (grouping === "year") {
        l = 4; // 2022
      }
      const label = item.aggregatedate.slice(0, l);
      labels.add(label);
    });

    labels.forEach(label => {
      deposits.push(
        data
          .filter(item => item.aggregatedate.slice(0, l) === label)
          .reduce((sum, item) => sum + item.deposits, 0)
      );
      withdrawals.push(
        data
          .filter(item => item.aggregatedate.slice(0, l) === label)
          .reduce((sum, item) => sum + item.withdrawals, 0)
      );
    });

    data = {
      labels: Array.from(labels),
      datasets: [
        {
          label: gettext("Deposits"),
          data: deposits,
          backgroundColor: "#227D7D",
        },
        {
          label: gettext("Withdrawals"),
          data: withdrawals,
          backgroundColor: "#D13838",
        },
      ],
    };

    return data;
  };

  const container = document.getElementById("transactionsGraphContainer");
  const graphcanvas = container.querySelector("#transactionsGraph");

  const Groupings = {
    day: gettext("daily"),
    month: gettext("monthly"),
    year: gettext("yearly"),
  };
  var buttonContainer = document.createElement("div");
  buttonContainer.className = "transactionGraphGroupingContainer";
  buttonContainer.onclick = function(event) {
    event.stopPropagation();
    event.preventDefault();
    var buttons = buttonContainer.querySelectorAll("a.btn");
    buttons.forEach(function(button) {
      button.classList.remove("btn-primary");
      button.classList.add("btn-secondary");
    });
    grouping = event.target.dataset.grouping;
    chart.options.scales.x.time.unit = event.target.dataset.grouping;
    chart.options.scales.x.time.round = event.target.dataset.grouping;
    (chart.data = buildGroupedDataGraphData(data, grouping)), chart.update();
    event.target.classList.remove("btn-secondary");
    event.target.classList.add("btn-primary");
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

  // default to showing grouped by month
  container
    .querySelector("#transactionGraphGrouping_month")
    .classList.remove("btn-secondary");
  container
    .querySelector("#transactionGraphGrouping_month")
    .classList.add("btn-primary");

  // render the chart
  chart = new Chart(graphcanvas, {
    type: "bar",
    data: buildGroupedDataGraphData(data, "month"),
    options: {
      borderWidth: 1,
      scales: {
        x: {
          type: "time",
          time: {
            unit: "month",
            round: "month",
          },
          stacked: true,
        },
      },
    },
  });
}
renderTransactionsGraph();
