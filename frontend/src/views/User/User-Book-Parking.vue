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
      <h2>Book a Parking Spot</h2><br/>

      <div v-if="message" class="alert" :class="{'alert-success': success, 'alert-danger': !success}">
        {{ message }}
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

              <ul class="list-group list-group-flush mb-3">
                <li v-for="spot in lot.spots" :key="spot.id" class="list-group-item">
                  Spot ID: {{ spot.id }} –
                  <span :class="spot.status === 'A' ? 'text-success' : 'text-danger'">
                    {{ spot.status === 'A' ? 'Available' : 'Reserved' }}
                  </span>
                </li>
              </ul>

              <button class="btn btn-primary"
                      :disabled="lot.available_spots === 0"
                      @click="openVehicleModal(lot.id)">
                {{ lot.available_spots === 0 ? 'Full' : 'Reserve Spot' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>


    <!-- 🚘 VEHICLE NUMBER MODAL -->
    <div class="modal fade show" v-if="showModal" style="display:block; background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content p-3">
          <h5>Enter Vehicle Number</h5>

          <input v-model="vehicleNumber" class="form-control" placeholder="TN09AB1234">

          <div class="mt-3 text-end">
            <button class="btn btn-secondary me-2" @click="closeModal">Cancel</button>
            <button class="btn btn-primary" @click="confirmReservation">Confirm</button>
          </div>
        </div>
      </div>
    </div>

</template>

<script>
import axios from 'axios';

export default {
  name: 'BookParking',
  data() {
    return {
      lots: [],
      message: '',
      success: true,
      username: localStorage.getItem('username'),

      showModal: false,
      selectedLotId: null,
      vehicleNumber: ""
    };
  },

  mounted() {
    this.fetchLots();
  },

  methods: {
    fetchLots() {
      const token = localStorage.getItem("authToken");

      axios.get('http://localhost:5000/api/user/parking-lots', {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => this.lots = res.data)
      .catch(() => {
        this.message = 'Error fetching parking lots';
        this.success = false;
      });
    },

    openVehicleModal(lotId) {
      this.selectedLotId = lotId;
      this.showModal = true;
    },

    closeModal() {
      this.showModal = false;
      this.vehicleNumber = "";
    },

    confirmReservation() {
      if (!this.vehicleNumber.trim()) {
        alert("Please enter vehicle number");
        return;
      }

      const token = localStorage.getItem("authToken");

      axios.post(
        "http://localhost:5000/api/user/allocate",
        {
          lot_id: this.selectedLotId,
          user: this.username,
          vehicle_no: this.vehicleNumber
        },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      .then(() => {
        this.message = "Spot reserved successfully!";
        this.success = true;

        this.closeModal();
        this.fetchLots();
      })
      .catch(err => {
        this.message = err.response?.data?.message || "Reservation failed";
        this.success = false;
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
.container {
  max-width: 1080px;
  margin: auto;
  padding: 2rem;
}
.login-wrapper {
  background: linear-gradient(to right, #4facfe, #00f2fe);
}
</style>
