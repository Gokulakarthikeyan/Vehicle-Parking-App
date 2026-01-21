<template>
  <div>
    <!-- Navbar -->
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

    <div class="container admin-dashboard">
      <h1 class="mb-4">Manage Parking Lots</h1>

      <!-- Add Parking Lot -->
      <section class="create-lot mb-5">
        <div class="card shadow-sm p-4 border-0">
          <h3 class="mb-4 text-primary fw-bold">Add Parking Lot</h3>

          <form @submit.prevent="createParkingLot" class="row g-4">
            <div class="col-md-4">
              <label class="form-label fw-semibold">Prime Location</label>
              <input v-model="newLot.prime_location_name" class="form-control form-control-lg" required />
            </div>
            <div class="col-md-2">
              <label class="form-label fw-semibold">Price (per/hr)</label>
              <input v-model.number="newLot.price" type="number" min="1" class="form-control form-control-lg" required />
            </div>
            <div class="col-md-4">
              <label class="form-label fw-semibold">Address</label>
              <input v-model="newLot.address" class="form-control form-control-lg" required />
            </div>
            <div class="col-md-2">
              <label class="form-label fw-semibold">Pin Code</label>
              <input v-model="newLot.pin_code" class="form-control form-control-lg" required />
            </div>
            <div class="col-md-2">
              <label class="form-label fw-semibold">Total Spots</label>
              <input v-model.number="newLot.number_of_spots" type="number" min="1" class="form-control form-control-lg" required />
            </div>
            <div class="col-md-2 d-flex align-items-end">
              <button type="submit" class="btn btn-primary btn-lg w-100 shadow-sm">Add Lot</button>
            </div>
          </form>
        </div>
      </section>

      <!-- List Parking Lots -->
      <section class="lots-display">
        <h3>Existing Parking Lots</h3>
        <div v-if="parkingLots.length === 0" class="alert alert-info">No parking lots added yet.</div>

        <div class="row">
          <div v-for="lot in parkingLots" :key="lot.id" class="col-md-6 mb-4">
            <div class="card shadow-sm">
              <div class="card-body">

                <!-- EDIT MODE -->
                <div v-if="editLotId === lot.id">
                  <h5 class="card-title">Editing {{ lot.prime_location_name }}</h5>
                  <input v-model="editForm.prime_location_name" class="form-control mb-2" />
                  <input v-model.number="editForm.price" type="number" class="form-control mb-2" />
                  <input v-model="editForm.address" class="form-control mb-2" />
                  <input v-model="editForm.pin_code" class="form-control mb-2" />
                  <input v-model.number="editForm.number_of_spots" type="number" class="form-control mb-3" />

                  <button class="btn btn-success me-2" @click="updateLot(lot.id)">Save</button>
                  <button class="btn btn-secondary" @click="cancelEdit">Cancel</button>
                </div>

                <!-- VIEW MODE -->
                <div v-else>
                  <h5 class="card-title">{{ lot.prime_location_name }}
                    <span v-if="lot.is_deleted" class="badge bg-danger ms-2">Disabled</span>
                  </h5>
                  <p class="card-text">
                    <strong>Price:</strong> ₹{{ lot.price }} <br />
                    <strong>Address:</strong> {{ lot.address }} <br />
                    <strong>Pin Code:</strong> {{ lot.pin_code }} <br />
                    <strong>Total Spots:</strong> {{ lot.number_of_spots }} <br />
                    <strong>Available Spots:</strong> {{ lot.available_spots }}
                  </p>
                  <h6 class="fw-bold mt-3">Parking Spots</h6>
                  <div class="row g-2">
                    <div v-for="spot in lot.spots" :key="spot.id" class="col-md-6">
                      <div class="spot-card p-2 rounded d-flex justify-content-between align-items-center"
                        :class="{
                          'bg-success-light': spot.status === 'A',
                          'bg-danger-light': spot.status === 'R',
                          'bg-secondary-light': spot.status === 'INACTIVE'
                        }">
                        <div>
                          <strong>Spot {{ spot.id }}</strong><br>
                          <small class="text-muted" v-if="spot.status === 'INACTIVE'">Inactive</small>

                          <span v-if="spot.status === 'A'" class="badge bg-success">Available</span>

                          <span v-if="spot.status === 'R'" class="badge bg-danger">
                            Reserved
                          </span>
                          <div v-if="spot.reserved_by" class="text-danger fw-semibold small">
                            by {{ spot.reserved_by }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <br />
                  <button class="btn btn-warning me-2" @click="startEdit(lot)" :disabled="lot.is_deleted">Edit</button>
                  <button v-if="!lot.is_deleted" class="btn btn-danger" @click="deleteLot(lot.id)">Delete</button>
                  <button v-else class="btn btn-success" @click="restoreLot(lot.id)">Restore</button>
                </div>

              </div>
            </div>
          </div>
        </div>

      </section>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { useToast } from "vue-toastification";

export default {
  name: "AdminDashboard",
  data() {
    return {
      newLot: {
        prime_location_name: "",
        price: 0,
        address: "",
        pin_code: "",
        number_of_spots: 0,
      },
      parkingLots: [],
      editLotId: null,
      editForm: {},
    };
  },
  setup() {
    const toast = useToast();
    return { toast };
  },
  methods: {
    async fetchLots() {
      try {
        const token = localStorage.getItem("authToken");
        const res = await axios.get("http://127.0.0.1:5000/api/admin/parking-lots", {
          headers: { Authorization: `Bearer ${token}` },
        });
        this.parkingLots = res.data;
      } catch (e) {
        console.error(e);
        this.toast.error("Failed to load parking lots.");
      }
    },

    async createParkingLot() {
      try {
        if (this.newLot.price <= 0 || this.newLot.number_of_spots <= 0) {
          this.toast.error("Price and number of spots must be positive!");
          return;
        }

        const token = localStorage.getItem("authToken");
        await axios.post("http://127.0.0.1:5000/api/admin/parking-lots", this.newLot, {
          headers: { Authorization: `Bearer ${token}` },
        });

        this.toast.success("Parking lot added!");
        this.newLot = { prime_location_name: "", price: 1, address: "", pin_code: "", number_of_spots: 1 };
        this.fetchLots();

      } catch (e) {
        this.toast.error(e.response?.data?.message || "Failed to create parking lot.");
      }
    },

    async restoreLot(lotId) {
      try {
        const token = localStorage.getItem("authToken");
        await axios.post(`http://127.0.0.1:5000/api/admin/parking-lots/${lotId}/restore`, {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.toast.success("Parking lot restored!");
        this.fetchLots();
      } catch (e) {
        console.error(e);
        this.toast.error(e.response?.data?.message || "Failed to restore parking lot.");
      }
    },

    startEdit(lot) {
      this.editLotId = lot.id;
      this.editForm = JSON.parse(JSON.stringify(lot));
    },

    cancelEdit() {
      this.editLotId = null;
      this.editForm = {};
    },

    async updateLot(lotId) {
      try {
        const token = localStorage.getItem("authToken");
        await axios.put(`http://127.0.0.1:5000/api/admin/parking-lots/${lotId}`, this.editForm, {
          headers: { Authorization: `Bearer ${token}` },
        });
        this.toast.success("Parking lot updated!");
        this.editLotId = null;
        this.fetchLots();
      } catch (e) {
        console.error("Update error:", e);
        this.toast.error(e.response?.data?.message || "Failed to update parking lot.");
      }
    },

    async deleteLot(lotId) {
      if (!confirm("Are you sure you want to delete this parking lot?")) return;
      try {
        const token = localStorage.getItem("authToken");
        await axios.delete(`http://127.0.0.1:5000/api/admin/parking-lots/${lotId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        this.toast.success("Parking lot deleted!");
        if (this.editLotId === lotId) this.cancelEdit();
        this.fetchLots();
      } catch (e) {
        const msg = e.response?.data?.message || "Failed to delete parking lot.";
        if (msg.includes("occupied")) this.toast.error("Cannot delete: Some spots are occupied or reserved!");
        else this.toast.error(msg);
      }
    },

    logout() {
      localStorage.removeItem("authToken");
      this.$router.push("/login");
    },
  },
  mounted() {
    this.fetchLots();
  },
};
</script>

<style scoped>
.admin-dashboard { padding: 1rem; }
.login-wrapper { background: linear-gradient(to right, #4facfe, #00f2fe); }
.card { border-radius: 10px; }
.create-lot .card { border-radius: 12px; }
.create-lot input { border-radius: 6px; padding: 6px 10px; font-size: 0.9rem; }
.create-lot h3 { font-size: 1.5rem; border-left: 5px solid #0d6efd; padding-left: 12px; }
.btn-primary { font-weight: 600; }
.text-success { font-weight: bold; }
.text-danger { font-weight: bold; }

.spot-card {
  min-height: 90px; /* Equal height cards */
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #ddd;
  text-align: left;
}

/* Backgrounds */
.bg-success-light {
  background-color: #e8f9f0;
  border-color: #b9e4c9;
}

.bg-danger-light {
  background-color: #fdecea;
  border-color: #f5c2c0;
}

.bg-secondary-light {
  background-color: #eeeeee;
  border-color: #d6d6d6;
}

</style>
