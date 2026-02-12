// Initialize map centered on New Delhi
let map = L.map('map').setView([28.6139, 77.2090], 13);

// Add OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
}).addTo(map);
// Store markers and data
let hospitalMarkers = [];
let ambulanceMarkers = [];
let currentFilter = 'all';
let hospitalsData = [];
let showAmbulances = true; // Always load ambulance data

// Tab switching
function switchTab(tab) {
    const hospitalPanel = document.getElementById('panelHospitals');
    const ambulancePanel = document.getElementById('panelAmbulances');
    const tabH = document.getElementById('tabHospitals');
    const tabA = document.getElementById('tabAmbulances');

    if (tab === 'hospitals') {
        hospitalPanel.style.display = 'block';
        ambulancePanel.style.display = 'none';
        tabH.classList.add('active');
        tabA.classList.remove('active');
    } else {
        hospitalPanel.style.display = 'none';
        ambulancePanel.style.display = 'block';
        tabH.classList.remove('active');
        tabA.classList.add('active');
    }
}

// Render ambulance list in sidebar
function renderAmbulanceList(ambulances) {
    const container = document.getElementById('ambulanceList');
    container.innerHTML = '';

    ambulances.forEach(amb => {
        const statusClass = amb.status === 'available' ? 'status-available'
                          : amb.status === 'en-route'  ? 'status-en-route'
                          : 'status-busy';
        const statusLabel = amb.status === 'available' ? 'Available'
                          : amb.status === 'en-route'  ? 'En-Route'
                          : 'Busy';
        const isAvailable = amb.status === 'available';

        const card = document.createElement('div');
        card.className = 'ambulance-card';
        card.id = `amb-card-${amb.id}`;
        card.innerHTML = `
            <div class="ambulance-header">
                <div class="ambulance-number">${amb.number}</div>
                <span class="status-pill ${statusClass}">${statusLabel}</span>
            </div>
            <div class="ambulance-meta">
                <svg width="13" height="13" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                </svg>
                Driver: <strong>${amb.driver}</strong>
            </div>
            <div class="ambulance-meta">
                <svg width="13" height="13" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.569 17.569 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328z"/>
                </svg>
                <a href="tel:${amb.phone}">${amb.phone}</a>
            </div>
            <div class="ambulance-meta">
                <svg width="13" height="13" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                </svg>
                ${amb.lat.toFixed(3)}, ${amb.lng.toFixed(3)}
            </div>
            <button class="book-ambulance-btn" ${!isAvailable ? 'disabled' : ''}
                onclick="bookAmbulanceFromList(${amb.id}, '${amb.number}', event)">
                🚑 Book Ambulance
            </button>
        `;

        // Click card (not button) → pan map to ambulance
        card.addEventListener('click', (e) => {
            if (e.target.closest('.book-ambulance-btn')) return;
            // Highlight card
            document.querySelectorAll('.ambulance-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            // Pan map and open popup
            map.setView([amb.lat, amb.lng], 16);
            ambulanceMarkers.forEach(marker => {
                if (marker.options.ambulanceId === amb.id) {
                    marker.openPopup();
                }
            });
        });

        container.appendChild(card);
    });
}

function bookAmbulanceFromList(ambId, ambNumber, e) {
    e.stopPropagation();
    
    // Find the ambulance data
    const ambulance = ambulanceMarkers.find(m => m.options.ambulanceId === ambId);
    if (!ambulance) {
        alert('❌ Error: Ambulance data not found');
        return;
    }
    
    const ambData = ambulance.options.ambulanceData;
    
    if (confirm(`Book ambulance ${ambNumber}?\n\nDriver: ${ambData.driver}\nPhone: ${ambData.phone}`)) {
        // Get user's current location
        if (navigator.geolocation) {
            console.log('📍 Requesting user location...');
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const userLat = position.coords.latitude;
                    const userLng = position.coords.longitude;
                    
                    console.log('✅ Location obtained:', userLat, userLng);
                    
                    const payload = {
                        ambulance_id: ambData.id,
                        ambulance_number: ambData.number,
                        driver: ambData.driver,
                        phone: ambData.phone,
                        lat: ambData.lat,
                        lng: ambData.lng,
                        driver_id: ambData.driver_id,  // Add driver_id
                        user_lat: userLat,
                        user_lng: userLng,
                        user_address: `${userLat.toFixed(6)}, ${userLng.toFixed(6)}`
                    };
                    
                    console.log('📤 Sending booking request:', payload);
                    
                    // Call the API with user location
                    fetch('/api/book_ambulance', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    })
                    .then(res => res.json())
                    .then(data => {
                        console.log('📥 Server response:', data);
                        if (data.success) {
                            alert(data.message);
                            // Redirect to Booking History modal
                            openBookingModal();
                        } else {
                            alert('❌ ' + (data.message || 'Booking failed'));
                        }
                    })
                    .catch(err => {
                        alert('❌ Network error. Please try again.');
                        console.error('Network error:', err);
                    });
                },
                (error) => {
                    console.error('❌ Geolocation error:', error);
                    alert('❌ Location access denied. Please enable location to book ambulance.');
                }
            );
        } else {
            alert('❌ Geolocation is not supported by your browser.');
        }
    }
}

// Custom marker HTML - SMALLER
function createHospitalMarker(available) {
    return L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="hospital-marker ${!available ? 'full' : ''}">H</div>`,
        iconSize: [36, 36],
        iconAnchor: [18, 18]
    });
}

function createAmbulanceMarker(status) {
    const bg = status === 'available' ? '#4CAF50' : status === 'en-route' ? '#f59e0b' : '#ef4444';
    return L.divIcon({
        className: 'custom-div-icon',
        html: `<div style="
            width:38px;height:38px;
            background:${bg};
            border-radius:10px;
            display:flex;align-items:center;justify-content:center;
            font-size:20px;
            box-shadow:0 2px 6px rgba(0,0,0,0.25);
            border:2px solid rgba(255,255,255,0.8);
        ">🚑</div>`,
        iconSize: [38, 38],
        iconAnchor: [19, 19]
    });
}

// Update statistics
function updateStats() {
    let totalBeds = 0;
    let availableBeds = 0;
    let fullCount = 0;

    hospitalsData.forEach(hospital => {
        const total = hospital.beds.icu + hospital.beds.general + hospital.beds.oxygen;
        totalBeds += total;
        availableBeds += (hospital.beds.icu + hospital.beds.general + hospital.beds.oxygen);

        if (total === 0) fullCount++;
    });

    document.getElementById('totalHospitals').textContent = hospitalsData.length;
    document.getElementById('availableBeds').textContent = `${availableBeds}/1448`;
    document.getElementById('fullHospitals').textContent = fullCount;
}

// Render hospital list
function renderHospitalList(hospitals) {
    const listContainer = document.getElementById('hospitalList');
    listContainer.innerHTML = '';

    hospitals.forEach(hospital => {
        const totalBeds = hospital.beds.icu + hospital.beds.general + hospital.beds.oxygen;
        const available = totalBeds > 0;

        const card = document.createElement('div');
        card.className = 'hospital-card';
        card.innerHTML = `
            <div class="hosp-card-top">
                <div class="hospital-name">${hospital.name}</div>
                <span class="hospital-badge ${available ? 'badge-available' : 'badge-full'}">
                    ${available ? 'Available' : 'Full'}
                </span>
            </div>
            <div class="hosp-meta-row">
                <div class="hospital-info">
                    <svg fill="currentColor" viewBox="0 0 16 16" width="12" height="12">
                        <path d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                    </svg>
                    ${hospital.lat.toFixed(3)}, ${hospital.lng.toFixed(3)}
                </div>
                <div class="hospital-info">
                    <svg fill="currentColor" viewBox="0 0 16 16" width="12" height="12">
                        <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.569 17.569 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328z"/>
                    </svg>
                    ${hospital.contact}
                </div>
            </div>
            <div class="bed-stats-row">
                <span class="bed-total-text">${totalBeds} beds</span>
                <span class="bed-dot">·</span>
                <span class="bed-stat-inline">ICU: <strong>${hospital.beds.icu}</strong></span>
                <span class="bed-stat-inline">General: <strong>${hospital.beds.general}</strong></span>
                <span class="bed-stat-inline">O₂: <strong>${hospital.beds.oxygen}</strong></span>
            </div>
            ${available ? `
                <button class="hospital-book-btn" data-hospital-id="${hospital.id}" data-hospital-name="${hospital.name}">
                    Book
                </button>
            ` : ''}
        `;

        // Click handler for card (excluding button)
        card.addEventListener('click', (e) => {
            // Don't trigger if clicking the book button
            if (e.target.classList.contains('hospital-book-btn')) {
                return;
            }

            // Remove previous selection
            document.querySelectorAll('.hospital-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');

            map.setView([hospital.lat, hospital.lng], 15);
            hospitalMarkers.forEach(marker => {
                if (marker.options.hospitalId === hospital.id) {
                    marker.openPopup();
                }
            });
        });

        // Book button handler
        const bookBtn = card.querySelector('.hospital-book-btn');
        if (bookBtn) {
            bookBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent card click
                window.location.href = `/booking?id=${hospital.id}`;
            });
        }

        listContainer.appendChild(card);
    });
}

// Load hospitals
async function loadHospitals() {
    try {
        const response = await fetch('/api/hospitals');
        hospitalsData = await response.json();

        // Clear existing hospital markers
        hospitalMarkers.forEach(marker => map.removeLayer(marker));
        hospitalMarkers = [];

        // Filter hospitals based on current filter
        let filteredHospitals = hospitalsData;
        if (currentFilter !== 'all') {
            filteredHospitals = hospitalsData.filter(h => h.beds[currentFilter] > 0);
        }

        filteredHospitals.forEach(hospital => {
            const totalBeds = hospital.beds.icu + hospital.beds.general + hospital.beds.oxygen;
            const hasBedsAvailable = totalBeds > 0;

            const marker = L.marker([hospital.lat, hospital.lng], {
                icon: createHospitalMarker(hasBedsAvailable),
                hospitalId: hospital.id
            }).bindPopup(`
                <div>
                    <div class="popup-header">
                        <div class="popup-icon">H</div>
                        <div class="popup-title">${hospital.name}</div>
                    </div>
                    <div class="popup-info">
                        <svg fill="currentColor" viewBox="0 0 16 16">
                            <path d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                        </svg>
                        ${hospital.address}
                    </div>
                    <div class="popup-info">
                        <svg fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.569 17.569 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328z"/>
                        </svg>
                        ${hospital.contact}
                    </div>
                    <div class="bed-grid">
                        <div class="bed-item ${hospital.beds.icu > 0 ? 'available' : 'full'}">
                            <div class="bed-count">${hospital.beds.icu}</div>
                            <div class="bed-label">ICU</div>
                        </div>
                        <div class="bed-item ${hospital.beds.general > 0 ? 'available' : 'full'}">
                            <div class="bed-count">${hospital.beds.general}</div>
                            <div class="bed-label">General</div>
                        </div>
                        <div class="bed-item ${hospital.beds.oxygen > 0 ? 'available' : 'full'}">
                            <div class="bed-count">${hospital.beds.oxygen}</div>
                            <div class="bed-label">Oxygen</div>
                        </div>
                    </div>
                    ${hasBedsAvailable ? `
                        <button onclick="requestBed(${hospital.id})" class="popup-btn">
                            <svg width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M3 5a2 2 0 0 0-2 2v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H3zm0 1h10a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z"/>
                            </svg>
                            Request Bed
                        </button>
                    ` : `
                        <button class="popup-btn" disabled>No Beds Available</button>
                    `}
                </div>
            `).addTo(map);

            hospitalMarkers.push(marker);
        });

        // Update sidebar list
        renderHospitalList(filteredHospitals);
        updateStats();

    } catch (error) {
        console.error('Error loading hospitals:', error);
    }
}

// Load ambulances - show on map + render sidebar list
async function loadAmbulances() {
    try {
        const response = await fetch('/api/ambulances');
        const ambulances = await response.json();

        // Clear existing ambulance markers
        ambulanceMarkers.forEach(marker => map.removeLayer(marker));
        ambulanceMarkers = [];

        // Count available ambulances
        const availableCount = ambulances.filter(a => a.status === 'available').length;
        document.getElementById('ambulancesReady').textContent = availableCount;

        ambulances.forEach(ambulance => {
            const marker = L.marker([ambulance.lat, ambulance.lng], {
                icon: createAmbulanceMarker(ambulance.status),
                ambulanceId: ambulance.id,
                ambulanceData: ambulance  // Store full ambulance data
            }).bindPopup(`
                <div>
                    <div class="popup-header">
                        <div class="popup-icon" style="background: ${ambulance.status === 'available' ? '#3b82f6' : ambulance.status === 'en-route' ? '#f59e0b' : '#ef4444'}">
                            🚑
                        </div>
                        <div class="popup-title">${ambulance.number}</div>
                    </div>
                    <div class="popup-info"><strong>Driver:</strong> ${ambulance.driver}</div>
                    <div class="popup-info"><strong>Phone:</strong> <a href="tel:${ambulance.phone}">${ambulance.phone}</a></div>
                    <div class="popup-info">
                        <strong>Status:</strong>
                        <span style="color: ${ambulance.status === 'available' ? '#059669' : ambulance.status === 'en-route' ? '#d97706' : '#dc2626'}; font-weight: 600; text-transform: uppercase;">
                            ${ambulance.status}
                        </span>
                    </div>
                </div>
            `).addTo(map);

            ambulanceMarkers.push(marker);
        });

        // Render ambulance list in sidebar
        renderAmbulanceList(ambulances);

    } catch (error) {
        console.error('Error loading ambulances:', error);
    }
}

// Request ambulance
function requestBed(hospitalId) {
    // Redirect to booking page for this hospital
    window.location.href = `/booking?hospital_id=${hospitalId}`;
}

// Filter functionality
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        loadHospitals();
    });
});

// Auto-refresh ambulance locations every 10 seconds (only if shown)
setInterval(loadAmbulances, 10000);

// Initial load
loadHospitals();
loadAmbulances();

// Check if should auto-open booking history modal
window.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('openBookings') === 'true') {
        // Small delay to ensure page is fully loaded
        setTimeout(() => {
            openBookingModal();
        }, 500);
    }
});


// ========================
// USER INFO MODAL
// ========================

function openUserModal() {
    const modal = new bootstrap.Modal(document.getElementById('userModal'));
    modal.show();

    // Fetch user info
    fetch('/api/user_info')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const user = data.data;
                const content = `
                    <div class="user-info-card">
                        <div class="user-avatar">
                            <svg width="80" height="80" fill="#9333ea" viewBox="0 0 16 16">
                                <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0zm4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4zm-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10z"/>
                            </svg>
                        </div>
                        <h4 style="margin: 15px 0 5px 0;">${user.name}</h4>
                        <p class="text-muted" style="margin-bottom: 25px;">Registered Member</p>

                        <div class="user-details">
                            <div class="user-detail-item">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                    <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.569 17.569 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328z"/>
                                </svg>
                                <div>
                                    <small class="text-muted">Phone Number</small>
                                    <div><strong>${user.phone}</strong></div>
                                </div>
                            </div>

                            <div class="user-detail-item">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                    <path d="M4 0a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H4zm0 1h8a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z"/>
                                    <path d="M3 5h10v1H3V5zm0 3h10v1H3V8zm0 3h10v1H3v-1z"/>
                                </svg>
                                <div>
                                    <small class="text-muted">Aadhar Number</small>
                                    <div><strong>${user.aadhar.substring(0, 4)} ${user.aadhar.substring(4, 8)} ${user.aadhar.substring(8)}</strong></div>
                                </div>
                            </div>

                            <div class="user-detail-item">
                                <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                    <path d="M11 6.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1z"/>
                                    <path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"/>
                                </svg>
                                <div>
                                    <small class="text-muted">Member Since</small>
                                    <div><strong>${new Date(user.registered_on).toLocaleDateString('en-US', {year: 'numeric', month: 'long', day: 'numeric'})}</strong></div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                document.getElementById('userInfoContent').innerHTML = content;
            }
        })
        .catch(err => {
            document.getElementById('userInfoContent').innerHTML = `
                <div class="alert alert-danger">Failed to load user information</div>
            `;
        });
}


// ========================
// BOOKING HISTORY MODAL
// ========================

function openBookingModal() {
    const modal = new bootstrap.Modal(document.getElementById('bookingModal'));
    modal.show();

    // Fetch booking history
    fetch('/api/booking_history')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderBedBookings(data.data.beds);
                renderAmbulanceBookings(data.data.ambulances);
            }
        })
        .catch(err => {
            document.getElementById('bedBookingsContent').innerHTML = `
                <div class="alert alert-danger">Failed to load booking history</div>
            `;
            document.getElementById('ambulanceBookingsContent').innerHTML = `
                <div class="alert alert-danger">Failed to load booking history</div>
            `;
        });
}

function renderBedBookings(bookings) {
    const container = document.getElementById('bedBookingsContent');

    if (bookings.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div style="font-size: 48px; opacity: 0.3;">🛏️</div>
                <p class="text-muted mt-3">No bed bookings yet</p>
            </div>
        `;
        return;
    }

    let html = '';
    bookings.forEach(booking => {
        const date = new Date(booking.booked_on);
        const statusClass = booking.status === 'confirmed' ? 'success' : 'warning';

        html += `
            <div class="booking-history-card">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">${booking.hospital_name}</h6>
                    <span class="badge bg-${statusClass}">${booking.status}</span>
                </div>
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3 1h10a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1z"/>
                        </svg>
                        <strong>Bed Type:</strong> ${booking.bed_type.toUpperCase()}
                    </small>
                </div>
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.569 17.569 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328z"/>
                        </svg>
                        <strong>Contact:</strong> ${booking.hospital_contact}
                    </small>
                </div>
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M11 6.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1z"/>
                            <path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"/>
                        </svg>
                        <strong>Booked:</strong> ${date.toLocaleString()}
                    </small>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderAmbulanceBookings(bookings) {
    const container = document.getElementById('ambulanceBookingsContent');

    if (bookings.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <div style="font-size: 48px; opacity: 0.3;">🚑</div>
                <p class="text-muted mt-3">No ambulance bookings yet</p>
            </div>
        `;
        return;
    }

    let html = '';
    bookings.forEach(booking => {
        const date = new Date(booking.booked_on);
        const statusClass = booking.status === 'accepted' ? 'success' :
                          booking.status === 'pending' ? 'warning' :
                          booking.status === 'denied' ? 'danger' :
                          booking.status === 'en-route' ? 'primary' :
                          booking.status === 'confirmed' ? 'success' : 'secondary';
        
        // Check if this is a standalone ambulance booking (has driver info)
        const isStandaloneBooking = booking.ambulance_driver !== undefined && booking.ambulance_driver !== null;

        html += `
            <div class="booking-history-card">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="mb-0">${isStandaloneBooking ? booking.ambulance_number : booking.hospital_name}</h6>
                    <span class="badge bg-${statusClass}">${booking.status}</span>
                </div>
        `;

        if (isStandaloneBooking) {
            // Standalone ambulance booking - show driver, phone, location
            html += `
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M0 3.5A1.5 1.5 0 0 1 1.5 2h9A1.5 1.5 0 0 1 12 3.5V5h1.02a1.5 1.5 0 0 1 1.17.563l1.481 1.85a1.5 1.5 0 0 1 .329.938V10.5a1.5 1.5 0 0 1-1.5 1.5H14a2 2 0 1 1-4 0H5a2 2 0 1 1-3.998-.085A1.5 1.5 0 0 1 0 10.5v-7z"/>
                        </svg>
                        <strong>Ambulance Number:</strong> ${booking.ambulance_number}
                    </small>
                </div>
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3 14s-1 0-1-1 1-4 6-4 6 3 6 4-1 1-1 1H3zm5-6a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                        </svg>
                        <strong>Driver:</strong> ${booking.ambulance_driver}
                    </small>
                </div>
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.569 17.569 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328z"/>
                        </svg>
                        <strong>Phone:</strong> <a href="tel:${booking.ambulance_phone}">${booking.ambulance_phone}</a>
                    </small>
                </div>
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 0 0-6 3 3 0 0 0 0 6z"/>
                        </svg>
                        <strong>Location:</strong> ${booking.ambulance_lat.toFixed(4)}, ${booking.ambulance_lng.toFixed(4)}
                    </small>
                </div>
            `;
        } else {
            // Hospital-based ambulance booking - show hospital info
            html += `
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M0 3.5A1.5 1.5 0 0 1 1.5 2h9A1.5 1.5 0 0 1 12 3.5V5h1.02a1.5 1.5 0 0 1 1.17.563l1.481 1.85a1.5 1.5 0 0 1 .329.938V10.5a1.5 1.5 0 0 1-1.5 1.5H14a2 2 0 1 1-4 0H5a2 2 0 1 1-3.998-.085A1.5 1.5 0 0 1 0 10.5v-7z"/>
                        </svg>
                        <strong>Service:</strong> ${booking.ambulance_number}
                    </small>
                </div>
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.569 17.569 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328z"/>
                        </svg>
                        <strong>Contact:</strong> ${booking.hospital_contact}
                    </small>
                </div>
            `;
        }

        html += `
                <div class="booking-meta">
                    <small>
                        <svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M11 6.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1z"/>
                            <path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"/>
                        </svg>
                        <strong>Booked:</strong> ${date.toLocaleString()}
                    </small>
                </div>
        `;

        if (isStandaloneBooking) {
            html += `
                <button class="btn btn-sm btn-outline-primary mt-2" onclick="viewAmbulanceLocation(${booking.ambulance_lat}, ${booking.ambulance_lng})">
                    📍 View on Map
                </button>
            `;
        } else {
            html += `
                <button class="btn btn-sm btn-outline-primary mt-2" onclick="trackAmbulance(${booking.id})">
                    📍 Track Ambulance
                </button>
            `;
        }

        html += `
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function trackAmbulance(bookingId) {
    const modal = new bootstrap.Modal(document.getElementById('trackModal'));
    modal.show();
}

function viewAmbulanceLocation(lat, lng) {
    // Close the booking modal
    const bookingModal = bootstrap.Modal.getInstance(document.getElementById('bookingModal'));
    if (bookingModal) {
        bookingModal.hide();
    }
    
    // Switch to ambulance tab if not already there
    switchTab('ambulances');
    
    // Pan map to the location
    map.setView([lat, lng], 16);
    
    // Find and highlight the ambulance marker at this location
    ambulanceMarkers.forEach(marker => {
        const markerLatLng = marker.getLatLng();
        // Check if marker is close to the booking location (within ~10 meters)
        if (Math.abs(markerLatLng.lat - lat) < 0.0001 && Math.abs(markerLatLng.lng - lng) < 0.0001) {
            marker.openPopup();
        }
    });
}