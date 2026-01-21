<template>
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

  <div class="container mt-4">
    <h2>Admin Search</h2>

    <input 
      type="text" 
      v-model="query" 
      @keyup.enter="performSearch" 
      class="form-control" 
      placeholder="Search users, parking lots, reservations..."
    />

    <button class="btn btn-primary mt-2" @click="performSearch">Search</button>

    <div v-if="loading" class="mt-3">Searching...</div>

    <div v-if="results">
      <!-- Users -->
      <h3 class="mt-4">Users</h3>
      <table class="table table-striped mt-3" v-if="results.users.length">
        <thead>
          <tr><th>Name</th><th>Email</th><th>Address</th><th>Pin</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in results.users" :key="u.id">
            <td>{{ u.name }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.address }}</td>
            <td>{{ u.pin_code }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>No users found.</p>

      <!-- Parking Lots -->
      <h3 class="mt-4">Parking Lots</h3>
      <table class="table table-striped mt-3" v-if="results.lots.length">
        <thead>
          <tr><th>Location</th><th>Address</th><th>Pin</th><th>Price</th><th>Status</th></tr>
        </thead>
        <tbody>
          <tr v-for="l in results.lots" :key="l.id">
            <td>{{ l.location }}</td>
            <td>{{ l.address }}</td>
            <td>{{ l.pin_code }}</td>
            <td>{{ l.price }}</td>
            <td>
              <span v-if="l.is_deleted" class="badge bg-danger">Disabled</span>
              <span v-else class="badge bg-success">Active</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else>No parking lots found.</p>

      <!-- Reservations -->
      <h3 class="mt-4">Reservations</h3>
      <table class="table table-striped mt-3" v-if="results.reservations.length">
        <thead>
          <tr>
            <th>User Name</th>
            <th>Parking Lot</th>
            <th>Spot</th>
            <th>Status</th>
            <th>Vehicle No.</th>
            <th>Start Time</th>
            <th>End Time</th>
            <th>Cost</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in results.reservations" :key="r.id">
            <td>{{ r.user.name }}</td>
            <td>{{ r.lot.name }}</td>
            <td>Spot {{ r.spot.id }}</td>
            <td>{{ r.status }}</td>
            <td>{{ r.Vehicle_no }}</td>
            <td>{{ r.formattedStart }}</td>
            <td>{{ r.formattedEnd }}</td>
            <td>{{ r.total_cost }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else>No reservations found.</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      query: "",
      results: null,
      loading: false
    };
  },

  methods: {
    // Convert timestamp into readable date
    formatDate(dateString) {
      if (!dateString) return "N/A";
      const date = new Date(dateString);
      return date.toLocaleString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    },

    async performSearch() {
      if (!this.query) {
        alert("Enter a search term");
        return;
      }

      this.loading = true;

      try {
        const token = localStorage.getItem("authToken");

        if (!token) {
          alert("You are not logged in. Please login again.");
          this.$router.push("/");
          return;
        }

        const res = await fetch(
          `http://localhost:5000/api/admin/search?q=${encodeURIComponent(this.query)}`,
          {
            headers: {
              "Authorization": `Bearer ${token}`,
              "Content-Type": "application/json"
            }
          }
        );

        if (!res.ok) {
          const backendText = await res.text();
          console.log("Backend error:", backendText);
          throw new Error("Server error");
        }

        let data = await res.json();

        // Format reservation dates
        if (data.reservations && Array.isArray(data.reservations)) {
          data.reservations = data.reservations.map(r => ({
            ...r,
            formattedStart: this.formatDate(r.start_time),
            formattedEnd: this.formatDate(r.end_time)
          }));
        }

        this.results = data;
      } catch (err) {
        console.error("Search error:", err);
        alert("Error fetching results");
      }

      this.loading = false;
    },

    logout() {
      localStorage.removeItem("authToken");
      localStorage.removeItem("username");
      localStorage.removeItem("role");
      this.$router.push("/");
    }
  }
};
</script>

<style scoped>
.login-wrapper {
  background: linear-gradient(to right, #4facfe, #00f2fe);
}
.card {
  border-radius: 10px;
}
.card h5 {
  font-weight: 600;
}
</style>
