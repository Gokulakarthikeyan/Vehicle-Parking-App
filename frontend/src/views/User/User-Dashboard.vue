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

    <div class="container mt-4">
      <h2>Welcome, {{ user.name || username }}</h2><br/>

    <!-- Available Parking Lots -->
    <section class="lots-display">
      <h3>Available Parking Lots</h3>

      <div v-if="lots.length === 0" class="alert alert-info">
        No parking lots available.<br/>
      </div>

      <div class="row">
        <div v-for="lot in lots" :key="lot.id" class="col-md-4 mb-4">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5 class="card-title">{{ lot.prime_location_name }}</h5>
              <p class="card-text">
                <strong>Price:</strong> ₹{{ lot.price }}/hr <br />
                <strong>Address:</strong> {{ lot.address }} <br />
                <strong>Pin Code:</strong> {{ lot.pin_code }} <br />
                <strong>Total Spots:</strong> {{ lot.number_of_spots }} <br />
                <strong>Available Spots:</strong> {{ lot.available_spots || 0 }}
              </p>

            </div>
          </div>
        </div>
      </div>
    </section>


      <!-- Active Reservations -->
      <div class="mt-5">
        <h4>Currently Active Reservations:</h4>
        <div v-if="reservations.length === 0" class="alert alert-info mt-3">
          No active reservations found.
        </div>

        <table v-else class="table table-striped mt-3">
          <thead>
            <tr>
              <th>Lot</th>
              <th>Spot ID</th>
              <th>Price/hr</th>
              <th>Vehicle No.</th>
              <th>Start Time</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="res in reservations" :key="res.reservation_id">
              <td>{{ res.lot_name }}</td>
              <td>{{ res.spot_id }}</td>
              <td>₹{{ res.price }}</td>
              <td>{{res.Vehicle_no}}</td>
              <td>{{ formatDate(res.start_time) }}</td>
              <td>{{ res.status }}</td>
              
              <td>
                <button
                  class="btn btn-danger btn-sm"
                  @click="terminateReservation(res.reservation_id)"
                >
                  Terminate
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
</template>

<script>
import axios from "axios";

export default {
  name: "UserDashboard",
  data() {
    return {
      username: localStorage.getItem("username") || "User",
      user: {},
      lots: [],
      reservations: [],
    };
  },
  mounted() {
    this.fetchUserDetails();
    this.fetchLots();
    this.fetchReservations();
  },
  methods: {
    async fetchUserDetails() {
      try {
        const res = await axios.get(`http://localhost:5000/api/user/details/${this.username}`);
        this.user = res.data;
      } catch (error) {
        console.error("Error fetching user details:", error);
      }
    },
    async fetchLots() {
      try {
        const res = await axios.get("http://localhost:5000/api/user/parking-lots");
        this.lots = res.data;
      } catch (error) {
        console.error("Error fetching lots:", error);
      }
    },
    async fetchReservations() {
      try {
        const res = await axios.get(
          `http://localhost:5000/api/user/reservations/${this.username}`
        );
        this.reservations = res.data;
      } catch (error) {
        console.error("Error fetching reservations:", error);
      }
    },
    async terminateReservation(reservationId) {
      if (!confirm("Are you sure you want to terminate this reservation?")) return;

      try {
        const res = await axios.post(
          `http://localhost:5000/api/user/reservations/terminate/${reservationId}`
        );

        alert("Reservation terminated successfully");

        // ⭐ AFTER TERMINATION → IMMEDIATELY INIT PAYMENT
        this.initiatePayment(reservationId);

        this.fetchReservations();
      } catch (error) {
        alert("Error terminating reservation: " + (error.response?.data?.message || error.message));
      }
    },

    async initiatePayment(reservationId) {
      try {
        const res = await axios.post("http://localhost:5000/api/payment/initiate", {
          reservation_id: reservationId
        });

        // dummy checkout link
        const url = res.data.payment_url;

        if (confirm(`Your total cost is ₹${res.data.amount}. Proceed to payment?`)) {
          window.location.href = url; // redirect to dummy payment page
        }

      } catch (err) {
        console.error(err);
        alert("Cannot initiate payment: " + (err.response?.data?.message || err.message));
      }
    },

    formatDate(dateStr) {
      if (!dateStr) return "N/A";
      const d = new Date(dateStr);
      return d.toLocaleString();
    },
    logout() {
      localStorage.removeItem("user_role");
      localStorage.removeItem("username");
      this.$router.push("/login");
    }
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
