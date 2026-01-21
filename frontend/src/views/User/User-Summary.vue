<template>
    <nav class="navbar navbar-expand-lg login-wrapper mb-4">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">User Dashboard</a>
        <ul class="navbar-nav">
          <li class="nav-item"> <router-link class="nav-link" to="/user/dashboard">Dashboard</router-link> </li>
          <li class="nav-item"> <router-link class="nav-link" to="/user/parking">Book a Spot</router-link> </li>
          <li class="nav-item"> <router-link class="nav-link" to="/user/summary">Summary</router-link> </li>
          <li class="nav-item"> <a class="nav-link" href="#" @click.prevent="logout">Logout</a> </li>
        </ul>
      </div>
    </nav>
  <div class="container py-4">

    <!-- Title -->
    <h2 class="mb-4">Parking Usage Summary</h2>

    <!-- SUMMARY CARDS -->
    <div class="row text-center mb-4">
      <div class="col-md-4">
        <div class="card shadow-sm p-3">
          <h5>Total Reservations</h5>
          <h3>{{ summary.total_reservations }}</h3>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card shadow-sm p-3">
          <h5>Total Hours Used</h5>
          <h3>{{ summary.total_hours }} hrs</h3>
        </div>
      </div>

      <div class="col-md-4">
        <div class="card shadow-sm p-3">
          <h5>Total Amount Spent</h5>
          <h3>₹{{ summary.total_cost }}</h3>
        </div>
      </div>
    </div>

    <!-- CHARTS SECTION -->
    <div class="row">

      <!-- Pie Chart -->
      <div class="col-md-4">
        <div class="card shadow-sm p-3">
          <h6 class="text-center">Reservation Status Distribution</h6>
          <canvas ref="pieChart"></canvas>
        </div>
      </div>

      <!-- Donut Chart -->
      <div class="col-md-4">
        <div class="card shadow-sm p-3">
          <h6 class="text-center">Spot Usage (Used vs Free)</h6>
          <canvas ref="donutChart"></canvas>
        </div>
      </div>

      <!-- Bar Chart -->
      <div class="col-md-4">
        <div class="card shadow-sm p-3">
          <h6 class="text-center">Monthly Usage Cost</h6>
          <canvas ref="barChart"></canvas>
        </div>
      </div>

    </div>

    <!-- HISTORY TABLE -->
    <div class="card shadow-sm mt-5 p-3">
      <h4>Reservation History</h4>
      <table class="table table-striped">
        <thead>
          <tr>
            <th>Lot</th>
            <th>Spot</th>
            <th>Status</th>
            <th>Vehicle No.</th>
            <th>Start</th>
            <th>End</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in history" :key="r.id">
            <td>{{ r.lot_name }}</td>
            <td>{{ r.spot_id }}</td>
            <td>
              <span :class="r.status === 'Reserved' ? 'text-success' : 'text-secondary'">
                {{ r.status }}
              </span>
            </td>
            <td>{{r.vehicle_no}}</td>
            <td>{{ formatDT(r.start_time) }}</td>
            <td>{{ r.end_time ? formatDT(r.end_time) : 'N/A' }}</td>
            <td>{{ r.total_cost ? '₹' + r.total_cost : 'N/A' }}</td>
          </tr>
        </tbody>
      </table>
    <button class="btn btn-primary mt-3" @click="downloadCSV">Download Reservation History</button>
    <button class="btn btn-success mt-3" @click="requestEmailExport">Email Whole CSV Export</button>
    </div>

  </div>
</template>

<script>
import axios from "axios";
import Chart from "chart.js/auto";

export default {
  data() {
    return {
      summary: {
        total_reservations: 0,
        total_cost: 0,
        total_hours: 0,
      },
      history: [],
      chartPie: null,
      chartDonut: null,
      chartBar: null
    };
  },

  methods: {
    formatDT(dt) {
      return new Date(dt).toLocaleString();
    },

    logout() {
      localStorage.removeItem("token");
      this.$router.push("/login");
    },

    async loadSummary() {
      try {
        const token = localStorage.getItem("authToken");

        const res = await axios.get("http://localhost:5000/api/user/summary", {
          headers: { Authorization: `Bearer ${token}` }
        });

        this.summary = res.data.summary;
        this.history = res.data.history;

        this.$nextTick(() => {
          this.renderCharts(res.data.graphs);
        });

      } catch (err) {
        console.error("Summary Load Error:", err);

        if (err.response && err.response.status === 401) {
          alert("Session expired. Please login again.");
          this.$router.push("/login");
        }
      }
    },

    async downloadCSV() {
      try {
        const token = localStorage.getItem("authToken");
        const username = localStorage.getItem("username");

        if (!username) {
          alert("Username missing. Please login again.");
          return;
        }

        const today = new Date().toISOString().split("T")[0];

        const response = await fetch(
          `http://localhost:5000/api/export-csv?username=${username}&date=${today}`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );

        if (!response.ok) {
          throw new Error("Failed to download CSV");
        }

        // ---- Filename extraction fix ----
        const disposition = response.headers.get("Content-Disposition");
        let filename = "history.csv";

        if (disposition) {
          const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
          if (match && match[1]) {
            filename = match[1].replace(/['"]/g, "");
          }
        }
        // ----------------------------------

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();

        window.URL.revokeObjectURL(url);
      } catch (err) {
        console.error("Download error:", err);
        alert("Download failed.");
      }
    },

    async requestEmailExport() {
      try {
        const username = localStorage.getItem("username");
        const token = localStorage.getItem("authToken");

        if (!username) {
          alert("Username missing. Please login again.");
          return;
        }

        const res = await fetch(
          `http://localhost:5000/api/user/export/${username}`,
          {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${token}`
            }
          }
        );

        const data = await res.json();

        if (res.status === 202) {
          alert("Your CSV is being prepared and will be emailed to you shortly.");
        } else {
          alert("Error: " + (data.message || "Failed to start export"));
        }

      } catch (err) {
        console.error("Email export error:", err);
        alert("Failed to start email export.");
      }
    },
    
    downloadHistory() {
        const username = localStorage.getItem("username"); // or res from API
        const today = new Date().toISOString().split("T")[0];
        this.downloadCSV(username, today);
    },

    renderCharts(graphs) {
      // Remove old charts
      if (this.chartPie) this.chartPie.destroy();
      if (this.chartDonut) this.chartDonut.destroy();
      if (this.chartBar) this.chartBar.destroy();

      // Pie Chart
      this.chartPie = new Chart(this.$refs.pieChart, {
        type: "pie",
        data: {
          labels: ["Reserved", "Released"],
          datasets: [{
            data: [graphs.reserved, graphs.released],
            backgroundColor: ["#28a745", "#6c757d"]
          }]
        }
      });

      // Donut Chart
      this.chartDonut = new Chart(this.$refs.donutChart, {
        type: "doughnut",
        data: {
          labels: ["Used Spots", "Free Spots"],
          datasets: [{
            data: [graphs.used_spots, graphs.free_spots],
            backgroundColor: ["#007bff", "#ffc107"]
          }]
        }
      });

      // Bar Chart
      this.chartBar = new Chart(this.$refs.barChart, {
        type: "bar",
        data: {
          labels: graphs.weeks,
          datasets: [{
            label: "₹ Cost",
            data: graphs.weekly_cost,
            backgroundColor: "#17a2b8"
          }]
        }
      });
    }
  },

  mounted() {
    this.loadSummary();
  }
};
</script>


<style scoped>
.container {
  padding: 2rem;
}
.login-wrapper {
  background: linear-gradient(to right, #4facfe, #00f2fe);
}
</style>
