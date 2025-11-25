import * as THREE from 'three';

// UI Manager class to handle all UI-related functionality
export class UIManager {
  constructor(scene, camera, renderer) {
    this.scene = scene;
    this.camera = camera;
    this.renderer = renderer;
    
    // Menu properties
    this.menu = null;
    this.raycaster = new THREE.Raycaster();
    this.intersectedObject = null;
    
    // Loading overlay
    this.loadingOverlay = null;
    this.isLoading = false;
  }
  
  // Create and setup the video selection menu
  createMenu(availableVideos, onVideoSelected) {
    // Remove existing menu if it exists
    if (this.menu) {
      this.scene.remove(this.menu);
    }
    
    this.menu = new THREE.Group();
    this.onVideoSelected = onVideoSelected;
    
    // Create background panel
    const panelGeometry = new THREE.PlaneGeometry(2, 1.5);
    const panelMaterial = new THREE.MeshBasicMaterial({
      color: 0x2c3e50,
      side: THREE.DoubleSide
    });
    const panel = new THREE.Mesh(panelGeometry, panelMaterial);
    this.menu.add(panel);
    
    // Create title
    this.createTextMesh("Select a Video", 0, 0.6, 0.08, 0xffffff).then(textMesh => {
      this.menu.add(textMesh);
    });
    
    // Add video options
    const buttonHeight = 0.15;
    const spacing = 0.2;
    const startY = 0.3;
    
    availableVideos.forEach((video, index) => {
      const y = startY - index * spacing;
      
      // Create button
      const buttonGeometry = new THREE.PlaneGeometry(1.2, buttonHeight);
      const buttonMaterial = new THREE.MeshBasicMaterial({
        color: 0x3498db,
        side: THREE.DoubleSide
      });
      const button = new THREE.Mesh(buttonGeometry, buttonMaterial);
      button.position.set(0, y, 0.01);
      button.name = `video-${index}`;
      this.menu.add(button);
      
      // Create label
      this.createTextMesh(video.displayName, 0, y, 0.05, 0xffffff).then(textMesh => {
        this.menu.add(textMesh);
      });
    });
    
    // Position menu in front of the camera
    this.menu.position.set(0, 0, -2);
    this.scene.add(this.menu);
    
    return this.menu;
  }
  
  // Helper function to create text meshes
  async createTextMesh(text, x, y, size, color) {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    const fontSize = 100;
    
    canvas.width = 512;
    canvas.height = 128;
    
    context.fillStyle = 'white';
    context.font = `bold ${fontSize}px Arial`;
    context.textAlign = 'center';
    context.textBaseline = 'middle';
    context.fillText(text, canvas.width / 2, canvas.height / 2);
    
    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      color: new THREE.Color(color)
    });
    
    const aspect = canvas.width / canvas.height;
    const geometry = new THREE.PlaneGeometry(size * aspect, size);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x, y, 0.02);
    
    return mesh;
  }
  
  // Check if controller is pointing at a menu item
  checkMenuIntersection(controller) {
    if (!this.menu || !this.menu.visible) return null;
    
    // Get controller direction
    const tempMatrix = new THREE.Matrix4();
    tempMatrix.identity().extractRotation(controller.matrixWorld);
    
    this.raycaster.ray.origin.setFromMatrixPosition(controller.matrixWorld);
    this.raycaster.ray.direction.set(0, 0, -1).applyMatrix4(tempMatrix);
    
    // Find intersections with menu buttons
    const intersects = this.raycaster.intersectObjects(this.menu.children, false);
    
    this.intersectedObject = null;
    
    // Reset button colors
    this.menu.children.forEach(child => {
      if (child.name && child.name.startsWith('video-')) {
        child.material.color.set(0x3498db);
      }
    });
    
    // Highlight intersected button
    if (intersects.length > 0) {
      const object = intersects[0].object;
      if (object.name && object.name.startsWith('video-')) {
        object.material.color.set(0x2ecc71);
        this.intersectedObject = object;
        return object;
      }
    }
    
    return null;
  }
  
  // Handle menu selection
  handleMenuSelection(controller) {
    const intersectedObject = this.checkMenuIntersection(controller);
    if (intersectedObject) {
      // Get the index from the name property
      const selectedIndex = parseInt(intersectedObject.name.split('-')[1]);
      if (!isNaN(selectedIndex) && this.onVideoSelected) {
        this.onVideoSelected(selectedIndex);
      }
    }
  }
  
  // Show menu
  showMenu() {
    if (this.menu) {
      this.menu.visible = true;
    }
  }
  
  // Hide menu
  hideMenu() {
    if (this.menu) {
      this.menu.visible = false;
    }
  }
  
  // Create a loading message in VR
  showLoadingMessage(message = "Loading...") {
    // Remove existing loading message if it exists
    if (this.loadingOverlay) {
      this.scene.remove(this.loadingOverlay);
    }
    
    this.loadingOverlay = new THREE.Group();
    
    // Create background panel
    const panelGeometry = new THREE.PlaneGeometry(1.5, 0.5);
    const panelMaterial = new THREE.MeshBasicMaterial({
      color: 0x000000,
      opacity: 0.7,
      transparent: true,
      side: THREE.DoubleSide
    });
    const panel = new THREE.Mesh(panelGeometry, panelMaterial);
    this.loadingOverlay.add(panel);
    
    // Create loading text
    this.createTextMesh(message, 0, 0, 0.06, 0xffffff).then(textMesh => {
      this.loadingOverlay.add(textMesh);
    });
    
    // Position in front of the camera
    this.loadingOverlay.position.set(0, 0, -2);
    this.scene.add(this.loadingOverlay);
    this.isLoading = true;
  }
  
  // Hide loading message
  hideLoadingMessage() {
    if (this.loadingOverlay) {
      this.scene.remove(this.loadingOverlay);
      this.loadingOverlay = null;
      this.isLoading = false;
    }
  }
  
  // Create a notification message that disappears after a few seconds
  showNotification(message, duration = 3000) {
    const notification = new THREE.Group();
    
    // Create background panel
    const panelGeometry = new THREE.PlaneGeometry(1.2, 0.3);
    const panelMaterial = new THREE.MeshBasicMaterial({
      color: 0x2c3e50,
      opacity: 0.8,
      transparent: true,
      side: THREE.DoubleSide
    });
    const panel = new THREE.Mesh(panelGeometry, panelMaterial);
    notification.add(panel);
    
    // Create notification text
    this.createTextMesh(message, 0, 0, 0.05, 0xffffff).then(textMesh => {
      notification.add(textMesh);
    });
    
    // Position at the bottom of the view
    notification.position.set(0, -0.6, -2);
    this.scene.add(notification);
    
    // Remove after duration
    setTimeout(() => {
      this.scene.remove(notification);
    }, duration);
    
    return notification;
  }
  
  // Create a help panel with controls information
  createHelpPanel() {
    const helpPanel = new THREE.Group();
    
    // Create background panel
    const panelGeometry = new THREE.PlaneGeometry(0.5, 0.6);
    const panelMaterial = new THREE.MeshBasicMaterial({
      color: 0x000000,
      opacity: 0.6,
      transparent: true,
      side: THREE.DoubleSide
    });
    const panel = new THREE.Mesh(panelGeometry, panelMaterial);
    helpPanel.add(panel);
    
    // Create title
    this.createTextMesh("Controls", 0, 0.23, 0.04, 0xffffff).then(textMesh => {
      helpPanel.add(textMesh);
    });
    
    // Create controls text
    const controls = [
      { text: "Trigger: Play/Pause", y: 0.13 },
      { text: "X Button: Menu", y: 0.03 },
      { text: "Point & Click", y: -0.07 },
      { text: "to select videos", y: -0.17 }
    ];
    
    controls.forEach(control => {
      this.createTextMesh(control.text, 0, control.y, 0.025, 0xffffff).then(textMesh => {
        helpPanel.add(textMesh);
      });
    });
    
    // Position to the side
    helpPanel.position.set(-1.5, 0, -2);
    helpPanel.rotation.y = Math.PI * 0.05; // Slight angle towards user
    
    return helpPanel;
  }
}