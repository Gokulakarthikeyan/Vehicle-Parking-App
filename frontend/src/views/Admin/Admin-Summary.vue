<template>
  <div>

    <!-- NAVIGATION -->
    <nav class="navbar navbar-expand-lg login-wrapper mb-4">
      <div class="container-fluid">
        <a class="navbar-brand" href="#">Admin Dashboard</a>
        <ul class="navbar-nav ms-auto">
          <li class="nav-item"><router-link class="nav-link" to="/admin/dashboard">Dashboard</router-link></li>
          <li class="nav-item"><router-link class="nav-link" to="/admin/view-user">View user</router-link></li>
          <li class="nav-item"><router-link class="nav-link" to="/admin/search">Search</router-link></li>
          <li class="nav-item"><router-link class="nav-link" to="/admin/summary">Summary</router-link></li>
          <li class="nav-item"><a class="nav-link" href="#" @click.prevent="logout">Logout</a></li>
        </ul>
      </div>
    </nav>

    <div class="container">

      <!-- ========================= SUMMARY CARDS ========================= -->
      <h2 class="text-center mb-4">Admin Summary Overview</h2>

      <div class="row g-4 mb-4">

        <!-- Total Spots -->
        <div class="col-md-3">
          <div class="summary-card shadow">
            <h4>{{ summary.total_spots }}</h4>
            <p>Total Spots</p>
          </div>
        </div>

        <!-- Reserved Spots -->
        <div class="col-md-3">
          <div class="summary-card shadow">
            <h4>{{ summary.reserved }}</h4>
            <p>Reserved Spots</p>
          </div>
        </div>

        <!-- Available Spots -->
        <div class="col-md-3">
          <div class="summary-card shadow">
            <h4>{{ summary.available }}</h4>
            <p>Available Spots</p>
          </div>
        </div>

        <!-- Total Revenue -->
        <div class="col-md-3">
          <div class="summary-card shadow">
            <h4>₹{{ summary.total_revenue }}</h4>
            <p>Total Revenue</p>
          </div>
        </div>
      </div>

      <!-- ========================= CHARTS GRID ========================= -->
      <div class="row g-4">

        <!-- Reserved vs Available -->
        <div class="col-md-5">
          <div class="card p-3 shadow chart-card">
            <h5>Parking Occupancy</h5>
            <canvas id="occupancyChart"></canvas>
          </div>
        </div>

        <!-- Revenue Per Lot -->
        <div class="col-md-7">
          <div class="card p-3 shadow chart-card">
            <h5>Revenue Per Parking Lot</h5>
            <canvas id="revenueChart"></canvas>
          </div>
        </div>

        <!-- Daily Revenue Trend -->
        <div class="col-md-6">
          <div class="card p-3 shadow chart-card">
            <h5>Daily Revenue (Last 10 Days)</h5>
            <canvas id="dailyRevenueChart"></canvas>
          </div>
        </div>

        <!-- Duration Distribution -->
        <div class="col-md-6">
          <div class="card p-3 shadow chart-card">
            <h5>Parking Duration Distribution</h5>
            <canvas id="durationChart"></canvas>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import Chart from "chart.js/auto";

export default {
  data() {
    return {
      token: localStorage.getItem("authToken"),

      summary: {
        total_spots: 0,
        reserved: 0,
        available: 0,
        total_revenue: 0
      }
    };
  },

  mounted() {
    this.loadSummary();
    this.loadCharts();
  },

  methods: {
    async loadSummary() {
      try {
        const headers = { Authorization: `Bearer ${this.token}` };

        const res = await axios.get("http://localhost:5000/api/admin/summary", { headers });

        const occ = res.data.occupancy;
        const rev = res.data.revenue_per_lot;

        const totalRevenue = rev.revenue.reduce((a, b) => a + b, 0);

        this.summary = {
          total_spots: occ.total,
          reserved: occ.reserved,
          available: occ.available,
          total_revenue: totalRevenue
        };

      } catch (err) {
        console.error("Summary load error:", err);
      }
    },

    async loadCharts() {
      try {
        const headers = { Authorization: `Bearer ${this.token}` };

        const res = await axios.get("http://localhost:5000/api/admin/summary", { headers });

        const occ = res.data.occupancy;
        const revLots = res.data.revenue_per_lot;
        const daily = res.data.daily_revenue;
        const duration = res.data.duration_distribution;

        this.drawOccupancyChart(occ);
        this.drawRevenueChart(revLots);
        this.drawDailyRevenueChart(daily);
        this.drawDurationChart(duration);

      } catch (err) {
        console.error("Chart load error:", err);
        alert("Failed to load summary charts");
      }
    },

    drawOccupancyChart(data) {
      new Chart(document.getElementById("occupancyChart"), {
        type: "pie",
        data: {
          labels: ["Reserved", "Available"],
          datasets: [
            {
              data: [data.reserved, data.available],
              backgroundColor: ["#ff4d6d", "#4dabf7"]
            }
          ]
        }
      });
    },

    drawRevenueChart(data) {
      new Chart(document.getElementById("revenueChart"), {
        type: "bar",
        data: {
          labels: data.lots,
          datasets: [
            {
              label: "Revenue (₹)",
              data: data.revenue,
              backgroundColor: "#4caf50"
            }
          ]
        }
      });
    },

    drawDailyRevenueChart(data) {
      new Chart(document.getElementById("dailyRevenueChart"), {
        type: "line",
        data: {
          labels: data.dates,
          datasets: [
            {
              label: "Revenue Per Day",
              data: data.values,
              borderColor: "#ff9800",
              tension: 0.4
            }
          ]
        }
      });
    },

    drawDurationChart(data) {
      new Chart(document.getElementById("durationChart"), {
        type: "bar",
        data: {
          labels: data.buckets,
          datasets: [
            {
              label: "Vehicles",
              data: data.counts,
              backgroundColor: "#9c27b0"
            }
          ]
        }
      });
    },

    logout() {
      localStorage.removeItem("authToken");
      this.$router.push("/login");
    }
  }
};
</script>


<style scoped>
/* Summary Cards */
.summary-card {
  background: white;
  padding: 20px;
  text-align: center;
  border-radius: 12px;
}

.summary-card h4 {
  font-size: 2rem;
  margin-bottom: 5px;
  color: #0072ff;
}

.summary-card p {
  font-size: 1rem;
  color: #555;
}

/* Chart Cards */
.chart-card {
  border-radius: 12px;
}

canvas {
  height: 300px !important;
}

.login-wrapper {
  background: linear-gradient(to right, #4facfe, #00f2fe);
}
</style>
