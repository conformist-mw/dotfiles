# homeassistant

Runs Home Assistant OS as a KVM/QEMU guest under libvirt on bee.

The Zigbee network is reached over IP (SLZB Ethernet coordinator), so the VM
needs no USB/PCI passthrough — only a bridged NIC.

## Behaviour

The role is **adopt-safe** and idempotent:

- Always ensures the host prerequisites (KVM/libvirt/OVMF/swtpm packages,
  `libvirtd`, user in the `libvirt`/`kvm` groups), plus the domain's autostart
  and running state.
- Provisions the VM (download + decompress the HAOS image, define the domain)
  **only when the domain is absent**. An existing domain is never redefined and
  its data disk is never touched.
- Leaves the network bridge alone unless `ha_manage_network: true` — editing
  netplan over SSH can drop connectivity.

## Disaster recovery

The qcow2 data disk, the swtpm state and the UEFI nvram are stateful and are
**not** reproducible from this role. HAOS encrypts its data partition with a
key bound to the emulated TPM, so a VM recreated with a new UUID cannot decrypt
an old disk. Recovery on a fresh host is therefore:

1. Run the role (with `ha_manage_network: true` if the bridge is not yet set up)
   to install a clean HAOS VM.
2. Restore from a Home Assistant backup through the onboarding screen.

## Bumping the HAOS image

HAOS self-updates from the UI, so `ha_image_version` only seeds fresh installs.
Bump it to match the running version when it matters for a clean reprovision.
