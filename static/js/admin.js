const token = localStorage.getItem('adminToken');
if (!token) window.location.href = '/secret-admin-panel';

window.onload = () => { loadDashboardStats(); loadPendingParking(); };

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.closest('.tab').classList.add('active');
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
    switch(tabName) {
        case 'pending': loadPendingParking(); break;
        case 'all-parking': loadAllParking(); break;
        case 'users': loadUsers(); break;
        case 'bookings': loadBookings(); break;
        case 'analytics': loadAreaWiseAnalytics(); break;
    }
}

function isExpired(availableTo) {
    return new Date(availableTo) < new Date();
}

async function loadDashboardStats() {
    try {
        const res = await fetch('/api/admin/dashboard', { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const data = await res.json();
            document.getElementById('totalUsers').textContent = data.users.total;
            document.getElementById('activeListings').textContent = data.parking_spaces.approved;
            document.getElementById('pendingApprovals').textContent = data.parking_spaces.pending;
            document.getElementById('pendingCount').textContent = data.parking_spaces.pending;
            document.getElementById('totalRevenue').textContent = `₹${data.revenue.total.toFixed(2)}`;
            document.getElementById('totalBookings').textContent = data.bookings.total;
        } else if (res.status === 403) {
            alert('Access denied'); localStorage.removeItem('adminToken'); window.location.href = '/secret-admin-panel';
        }
    } catch (e) { console.error(e); }
}

async function loadPendingParking() {
    const c = document.getElementById('pendingTableContainer');
    c.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i><p>Loading...</p></div>';
    try {
        const res = await fetch('/api/admin/parking/pending', { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const data = await res.json();
            if (data.parking_spaces.length === 0) {
                c.innerHTML = '<div class="empty-state"><i class="fas fa-check-circle"></i><p>No pending approvals</p></div>';
                return;
            }
            let html = '<table><thead><tr><th>Details</th><th>Owner</th><th>Pricing & Timing</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            data.parking_spaces.forEach(p => {
                const exp = isExpired(p.available_to);
                const from = new Date(p.available_from);
                const to = new Date(p.available_to);
                // Check if this is an edited listing
                const isEdited = p.is_edited === true;
                const editedBadge = isEdited ? '<span class="badge" style="background:#fbbf24;color:#78350f;margin-left:0.5rem"><i class="fas fa-edit"></i> EDITED</span>' : '';
                html += `<tr><td><strong>${p.title}</strong>${editedBadge}<br><small>${p.address}</small><br><span class="badge active">${p.vehicle_type}</span></td>
                <td><strong>${p.owner.name}</strong><br><small>${p.owner.email}</small><br><small>${p.owner.phone}</small></td>
                <td>₹${p.price_per_hour}/hr<br><small>${from.toLocaleString()}</small><br><small>to ${to.toLocaleString()}</small>${exp ? '<div class="expiry-warning"><i class="fas fa-exclamation-triangle"></i> Expired</div>' : ''}</td>
                <td><span class="badge ${exp ? 'expired' : 'pending'}">${exp ? 'Expired' : 'Pending'}</span>${editedBadge}<br><small>${new Date(p.created_at).toLocaleDateString()}</small></td>
                <td><div class="action-btns"><button class="btn btn-view" onclick="viewParkingDetails('${p.id}')"><i class="fas fa-eye"></i> View</button>
                <button class="btn btn-approve" onclick="approveParking('${p.id}')" ${exp ? 'disabled style="opacity:0.5"' : ''}><i class="fas fa-check"></i> Approve${isEdited ? ' Edit' : ''}</button>
                <button class="btn btn-reject" onclick="rejectParking('${p.id}')"><i class="fas fa-times"></i> Reject</button></div></td></tr>`;
            });
            c.innerHTML = html + '</tbody></table>';
        }
    } catch (e) { console.error(e); c.innerHTML = '<div class="empty-state"><p>Error loading data</p></div>'; }
}

async function loadAllParking() {
    const c = document.getElementById('allParkingContainer');
    c.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i><p>Loading...</p></div>';
    try {
        const res = await fetch('/api/admin/parking/all', { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const data = await res.json();
            if (data.parking_spaces.length === 0) {
                c.innerHTML = '<div class="empty-state"><i class="fas fa-parking"></i><p>No parking spaces</p></div>';
                return;
            }
            let html = '<table><thead><tr><th>Title</th><th>Owner</th><th>Address</th><th>Type</th><th>Price/Hr</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            data.parking_spaces.forEach(p => {
                const exp = isExpired(p.available_to);
                const displayStatus = (p.status === 'approved' && exp) ? 'expired' : p.status;
                const statusText = (p.status === 'approved' && exp) ? 'Expired' : p.status;
                html += `<tr><td><strong>${p.title}</strong></td><td>${p.owner.name}</td><td>${p.address}</td>
                <td><span class="badge active">${p.vehicle_type}</span></td><td>₹${p.price_per_hour}</td>
                <td><span class="badge ${displayStatus}">${statusText}</span></td>
                <td><button class="btn btn-view" onclick="viewParkingDetails('${p.id}')"><i class="fas fa-eye"></i> View</button></td></tr>`;
            });
            c.innerHTML = html + '</tbody></table>';
        }
    } catch (e) { console.error(e); c.innerHTML = '<div class="empty-state"><p>Error loading data</p></div>'; }
}

async function loadUsers() {
    const c = document.getElementById('usersContainer');
    c.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i><p>Loading...</p></div>';
    try {
        const res = await fetch('/api/admin/users', { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const data = await res.json();
            if (data.users.length === 0) {
                c.innerHTML = '<div class="empty-state"><i class="fas fa-users"></i><p>No users</p></div>';
                return;
            }
            let html = '<table><thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Role</th><th>Status</th><th>Joined</th><th>Actions</th></tr></thead><tbody>';
            data.users.forEach(u => {
                html += `<tr><td><strong>${u.name}</strong></td><td>${u.email}</td><td>${u.phone || 'N/A'}</td>
                <td><span class="badge ${u.role === 'admin' ? 'approved' : 'active'}">${u.role}</span></td>
                <td><span class="badge ${u.is_active ? 'approved' : 'rejected'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>${new Date(u.created_at).toLocaleDateString()}</td>
                <td><button class="btn btn-view" onclick="viewUserDetails('${u.id}')"><i class="fas fa-eye"></i> View</button></td></tr>`;
            });
            c.innerHTML = html + '</tbody></table>';
        }
    } catch (e) { console.error(e); c.innerHTML = '<div class="empty-state"><p>Error loading data</p></div>'; }
}

async function loadBookings() {
    const c = document.getElementById('bookingsContainer');
    c.innerHTML = '<div class="loading"><i class="fas fa-spinner"></i><p>Loading...</p></div>';
    try {
        const res = await fetch('/api/admin/bookings', { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const data = await res.json();
            if (data.bookings.length === 0) {
                c.innerHTML = '<div class="empty-state"><i class="fas fa-calendar"></i><p>No bookings</p></div>';
                return;
            }
            let html = '<table><thead><tr><th>ID</th><th>Parking</th><th>Renter</th><th>Owner</th><th>Amount</th><th>Duration</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            data.bookings.forEach(b => {
                html += `<tr><td><small>${b.id.substring(0, 8)}...</small></td><td><strong>${b.parking.title}</strong></td>
                <td>${b.user.name}</td><td>${b.owner.name}</td>
                <td><span class="payment-badge">₹${b.total_price}</span></td><td>${b.duration_hours || "N/A"} hrs</td>
                <td><span class="badge ${b.status}">${b.status}</span></td>
                <td><button class="btn btn-view" onclick="viewBookingDetails('${b.id}')"><i class="fas fa-eye"></i> View</button></td></tr>`;
            });
            c.innerHTML = html + '</tbody></table>';
        }
    } catch (e) { console.error(e); c.innerHTML = '<div class="empty-state"><p>Error loading data</p></div>'; }
}

async function viewParkingDetails(id) {
    try {
        const res = await fetch(`/api/parking/${id}`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const d = await res.json(), p = d.parking, o = d.owner;
            const from = new Date(p.available_from), to = new Date(p.available_to), exp = isExpired(p.available_to);
            let html = `<div class="detail-row"><div class="detail-label">Title:</div><div class="detail-value"><strong>${p.title}</strong></div></div>
            <div class="detail-row"><div class="detail-label">Description:</div><div class="detail-value">${p.description || 'N/A'}</div></div>
            <div class="detail-row"><div class="detail-label">Address:</div><div class="detail-value">${p.address}</div></div>
            <div class="detail-row"><div class="detail-label">Vehicle Type:</div><div class="detail-value"><span class="badge active">${p.vehicle_type}</span></div></div>
            <div class="detail-row"><div class="detail-label">Total Spaces:</div><div class="detail-value">${p.total_spaces || 1}</div></div>
            <div class="detail-row"><div class="detail-label">Price/Hour:</div><div class="detail-value"><strong>₹${p.price_per_hour}</strong></div></div>
            <div class="detail-row"><div class="detail-label">Available From:</div><div class="detail-value">${from.toLocaleString()}</div></div>
            <div class="detail-row"><div class="detail-label">Available To:</div><div class="detail-value">${to.toLocaleString()}</div></div>
            ${exp ? '<div class="expiry-warning"><i class="fas fa-exclamation-triangle"></i> This listing has expired</div>' : ''}
            <div class="detail-row"><div class="detail-label">Status:</div><div class="detail-value"><span class="badge ${exp ? 'expired' : p.status}">${exp ? 'Expired' : p.status}</span></div></div>
            <div class="detail-row"><div class="detail-label">Payment Methods:</div><div class="detail-value">${p.payment_methods ? p.payment_methods.join(', ') : 'N/A'}</div></div>
            <h3 style="margin-top:1.5rem;margin-bottom:1rem">Owner Info</h3>
            <div class="detail-row"><div class="detail-label">Name:</div><div class="detail-value">${o.name}</div></div>
            <div class="detail-row"><div class="detail-label">Email:</div><div class="detail-value">${o.email}</div></div>
            <div class="detail-row"><div class="detail-label">Phone:</div><div class="detail-value">${p.owner_phone || o.phone || 'N/A'}</div></div>`;
            if (p.images && p.images.length > 0) {
                html += '<h3 style="margin-top:1.5rem;margin-bottom:1rem">Images</h3>';
                p.images.forEach(img => {
                    // Handle both absolute and relative URLs
                    const imgSrc = img.startsWith('http') ? img : (img.startsWith('/') ? img : `/${img}`);
                    html += `<img src="${imgSrc}" class="parking-image" alt="Parking space" onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
                    <div style="display:none;padding:1rem;background:#fee2e2;color:#991b1b;border-radius:8px;margin:1rem 0;">Image failed to load: ${img}</div>`;
                });
            }
            document.getElementById('parkingDetails').innerHTML = html;
            document.getElementById('parkingModal').classList.add('show');
        }
    } catch (e) { alert('Failed to load details'); console.error(e); }
}

async function viewUserDetails(id) {
    try {
        const res = await fetch(`/api/admin/users/${id}`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const d = await res.json(), u = d.user, s = d.stats || {};
            let html = `<div class="detail-row"><div class="detail-label">Name:</div><div class="detail-value"><strong>${u.name}</strong></div></div>
            <div class="detail-row"><div class="detail-label">Email:</div><div class="detail-value">${u.email}</div></div>
            <div class="detail-row"><div class="detail-label">Phone:</div><div class="detail-value">${u.phone || 'N/A'}</div></div>
            <div class="detail-row"><div class="detail-label">Role:</div><div class="detail-value"><span class="badge ${u.role === 'admin' ? 'approved' : 'active'}">${u.role}</span></div></div>
            <div class="detail-row"><div class="detail-label">Status:</div><div class="detail-value"><span class="badge ${u.is_active ? 'approved' : 'rejected'}">${u.is_active ? 'Active' : 'Inactive'}</span></div></div>
            <div class="detail-row"><div class="detail-label">Verified:</div><div class="detail-value">${u.is_verified ? 'Yes' : 'No'}</div></div>
            <div class="detail-row"><div class="detail-label">Joined:</div><div class="detail-value">${new Date(u.created_at).toLocaleString()}</div></div>
            <h3 style="margin-top:1.5rem;margin-bottom:1rem">Activity</h3>
            <div class="user-info">
                <div class="user-info-item"><span>Parking Spaces:</span><strong>${s.parking_spaces || 0}</strong></div>
                <div class="user-info-item"><span>Bookings Made:</span><strong>${s.bookings_made || 0}</strong></div>
                <div class="user-info-item"><span>Bookings Received:</span><strong>${s.bookings_received || 0}</strong></div>
                <div class="user-info-item"><span>Total Spent:</span><strong>₹${s.total_spent || 0}</strong></div>
                <div class="user-info-item"><span>Total Earned:</span><strong>₹${s.total_earned || 0}</strong></div>
            </div>`;
            document.getElementById('userDetails').innerHTML = html;
            document.getElementById('userModal').classList.add('show');
        }
    } catch (e) { alert('Failed to load details'); console.error(e); }
}

async function viewBookingDetails(id) {
    try {
        const res = await fetch(`/api/admin/bookings/${id}`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const d = await res.json(), b = d.booking;
            let html = `<div class="detail-row"><div class="detail-label">ID:</div><div class="detail-value"><code>${b.id}</code></div></div>
            <div class="detail-row"><div class="detail-label">Parking:</div><div class="detail-value"><strong>${b.parking.title}</strong></div></div>
            <div class="detail-row"><div class="detail-label">Renter:</div><div class="detail-value">${b.user.name} (${b.user.email})</div></div>
            <div class="detail-row"><div class="detail-label">Owner:</div><div class="detail-value">${b.owner.name} (${b.owner.email})</div></div>
            <div class="detail-row"><div class="detail-label">Start:</div><div class="detail-value">${new Date(b.start_time).toLocaleString()}</div></div>
            <div class="detail-row"><div class="detail-label">End:</div><div class="detail-value">${new Date(b.end_time).toLocaleString()}</div></div>
            <div class="detail-row"><div class="detail-label">Duration:</div><div class="detail-value">${b.duration_hours || "N/A"} hours</div></div>
            <div class="detail-row"><div class="detail-label">Amount:</div><div class="detail-value"><span class="payment-badge">₹${b.total_price}</span></div></div>
            <div class="detail-row"><div class="detail-label">Payment:</div><div class="detail-value">${b.payment_method || 'N/A'}</div></div>
            <div class="detail-row"><div class="detail-label">Status:</div><div class="detail-value"><span class="badge ${b.status}">${b.status}</span></div></div>
            <div class="detail-row"><div class="detail-label">Created:</div><div class="detail-value">${new Date(b.created_at).toLocaleString()}</div></div>`;
            document.getElementById('bookingDetails').innerHTML = html;
            document.getElementById('bookingModal').classList.add('show');
        }
    } catch (e) { alert('Failed to load details'); console.error(e); }
}

async function approveParking(id) {
    if (!confirm('Approve this parking space?')) return;
    try {
        const res = await fetch(`/api/admin/parking/${id}/approve`, {
            method: 'POST', headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) { alert('Approved!'); loadDashboardStats(); loadPendingParking(); }
        else { const e = await res.json(); alert(e.error || 'Failed'); }
    } catch (e) { alert('Error approving'); console.error(e); }
}

async function rejectParking(id) {
    const reason = prompt('Rejection reason (optional):');
    try {
        const res = await fetch(`/api/admin/parking/${id}/reject`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason || '' })
        });
        if (res.ok) { alert('Rejected'); loadDashboardStats(); loadPendingParking(); }
        else { const e = await res.json(); alert(e.error || 'Failed'); }
    } catch (e) { alert('Error rejecting'); console.error(e); }
}

function closeModal(id) { document.getElementById(id).classList.remove('show'); }
function logout() { localStorage.removeItem('adminToken'); localStorage.removeItem('admin'); window.location.href = '/secret-admin-panel'; }
