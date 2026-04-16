# Philips Hue Play HDMI Sync Box

Home Assistant integration for the Philips Hue Play HDMI Sync Box (4K and 8K).

[![Checks](https://img.shields.io/github/actions/workflow/status/mvdwetering/huesyncbox/push.yaml?branch=dev&label=checks)](https://github.com/mvdwetering/huesyncbox/actions/workflows/push.yaml)
[![Latest release](https://img.shields.io/github/v/release/mvdwetering/huesyncbox?sort=semver)](https://github.com/mvdwetering/huesyncbox/releases)
[![HA version](https://img.shields.io/badge/Home%20Assistant-%E2%89%A5%202025.12.0-41BDF5?logo=home-assistant&logoColor=white)](https://github.com/home-assistant/core)
[![License](https://img.shields.io/github/license/mvdwetering/huesyncbox)](./LICENSE)
[![Contributors](https://img.shields.io/github/contributors/mvdwetering/huesyncbox.svg)](https://github.com/mvdwetering/huesyncbox/graphs/contributors)

- [About](#about)
- [Supported devices](#supported-devices)
- [Possible use-cases](#possible-use-cases)
- [Entities](#entities)
  - [Behavior](#behavior)
- [Data updates](#data-updates)
- [Actions](#actions)
  - [Set bridge](#set-bridge)
  - [Set sync state](#set-sync-state)
- [Installation](#installation)
- [Removal](#removal)

## About

> Please set up the Philips Hue Play HDMI Sync Box with the Hue App first and make sure it works before setting up this integration.

This integration allows you to control and automate your Philips Hue Play HDMI Sync Box from Home Assistant. Use it in automations, dashboards, and scripts to improve your entertainment experience.

## Supported devices

Both the 4K and 8K models are supported.

## Possible use-cases

- Start light syncing in specific cases (e.g., when a specific app is running, or only after dark)
- Turn the box on and control the selected input based on which devices are on (useful if the automatic switching can not be used)
- Automate actions when light syncing starts (e.g., dim other lights, close blinds)

## Entities

### Controls

| Entity | Platform | Description |
|---|---|---|
| Power | Switch | Toggle the box between powersave and passthrough |
| Light sync | Switch | Start/stop syncing lights with HDMI content |
| Sync mode | Select | `video` / `music` / `game` |
| Intensity | Select | `subtle` / `moderate` / `high` / `intense` (per sync mode) |
| HDMI input | Select | Switch the active HDMI input |
| Entertainment area | Select | Select the Hue entertainment area to sync with |
| Brightness | Number | 1–100 slider |

### Configuration

| Entity | Platform | Description |
|---|---|---|
| LED indicator | Select | `off` / `normal` / `dimmed` |
| Dolby Vision compatibility | Switch | Force native DV mode (4K model only) |

### Diagnostic

| Entity | Platform | Default | Description |
|---|---|---|---|
| HDMI 1–4 status | Sensor | Enabled | Connection state of each input (`unplugged`, `plugged`, `linked`, `unknown`) |
| HDMI output status | Sensor | Enabled | Connection state of the HDMI output (useful to detect TV on/off) |
| Content info | Sensor | Disabled | Resolution and HDR of the active input (e.g. `3840 x 2160 @ 60000 - HDR`) |
| Bridge connection | Sensor | Disabled | State of the link to the Hue bridge |
| Bridge ID | Sensor | Disabled | Unique ID of the connected Hue bridge |
| Bridge IP address | Sensor | Disabled | IP of the connected Hue bridge |
| IP address | Sensor | Disabled | IP of the sync box itself |
| Wi-Fi quality | Sensor | Disabled | Wi-Fi signal strength (`weak`…`excellent`) |
| API level | Sensor | Disabled | Device API version — useful when reporting issues |

### Behavior

A few notes on behavior when changing entities. This behavior is just how the box reacts when sending these commands, not something explicitly coded in this integration.

- Enabling light sync will also power on the box
- Setting sync mode will also power on the box and start light sync on the selected mode
- When changing multiple entities the order is important. For example, Intensity applies to the current selected mode. So if you want to change both the `intensity` and `mode` you _first_ have to change the mode and then set the intensity. Otherwise, the intensity is applied to the "old" mode. To avoid ordering issues use the [`set_sync_state` action](#set-sync-state) which will take care of the ordering and is more efficient than sending everything separately.

## Data updates

This integration polls the Philips Hue Play HDMI Sync Box every 3 seconds.

## Actions

The integration exposes two additional actions.

### Set bridge

This action allows setting the bridge to be used by the Philips Hue Play HDMI Sync Box. For example when you have 2 different bridges you want to sync to and need to switch.

Note that changing the bridge by the box takes a while (about 15 seconds it seems). After the bridge has changed you might need to (re)select the `entertainment_area` if connectionstate is `invalidgroup` instead of `connected`.

| Parameter | Optional | Description |
| --- | --- | --- |
| device_id | No | Home Assistant device ID of the Philips Hue Play HDMI Sync Box. |
| bridge_id | Yes | ID of the bridge. A hexadecimal code of 16 characters. |
| bridge_username | Yes | Username (a.k.a. application key) valid for the bridge. A long code of random characters. |
| bridge_clientkey | Yes | Client key that belongs with the username. A hexadecimal code of 32 characters. |

YAML action call example:

```yaml
action: huesyncbox.set_bridge
data:
  device_id: 11223344556677889900aabbccddeeff
  bridge_id: 001788FFFE000000
  bridge_username: abcdefghijklmnopqrstuvwxyz1234567890ABCD
  bridge_clientkey: 00112233445566778899AABBCCDDEEFF
```

### Set sync state

Set the state of multiple entities of the Philips Hue Play HDMI Sync Box at once. Using this action makes sure everything is set in the correct order and is more efficient than using separate commands.

| Parameter | Optional | Description |
| --- | --- | --- |
| device_id | No | Home Assistant device ID of the Philips Hue Play HDMI Sync Box. |
| power | Yes | Turn the box on or off. |
| sync | Yes | Set light sync state on or off. Setting this to on will also turn on the box. |
| brightness | Yes | Brightness value to set. |
| intensity | Yes | Intensity to set. |
| mode | Yes | Mode to set. Setting the mode will also turn on the box and start light sync. |
| input | Yes | Input to select. |
| entertainment_area | Yes | Entertainment area to select. Name must match _exactly_. |

YAML action call example:

```yaml
action: huesyncbox.set_sync_state
data:
  device_id: 11223344556677889900aabbccddeeff
  power: true
  sync: true
  brightness: 42
  intensity: high
  mode: video
  input: input1
  entertainment_area: "TV Area"
```

## Installation

> Please set up the Philips Hue Play HDMI Sync Box with the Hue App first and make sure it works before setting up this integration.

### Downloading

#### Home Assistant Community Store (HACS)

> HACS is a third-party downloader for Home Assistant to easily install and update custom integrations made by the community. See <https://hacs.xyz/> for more details.

You can add this repository to HACS on your Home Assistant instance with the button below.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mvdwetering&repository=huesyncbox&category=integration)

If the button does not work, or you don't want to use it, follow these steps to add the integration to HACS manually.

<details>
<summary>Manual HACS configuration steps</summary>

- Go to your Home Assistant instance
- Open the HACS page
- Search for "Philips Hue HDMI Sync Box" in the HACS search bar
- Click/tap on the integration to open the integration page
- Press the Download button to download the integration
- **Restart Home Assistant**

</details>

#### Manual download

- Go to the [releases section on GitHub](https://github.com/mvdwetering/huesyncbox/releases)
- Download the zip file for the version you want to install
- Extract the zip
- Ensure the `config/custom_components/huesyncbox` directory exists (create it if needed)
- Copy the files from the zip into the `config/custom_components/huesyncbox` directory
- **Restart Home Assistant**

### Configuration

The Philips Hue Play HDMI Sync Box will be discovered automatically in most cases. If not, add it manually via `Settings > Devices and Services` in Home Assistant.

For manual configuration, provide the following parameters (found in the Hue app's sync box device settings):

**IP Address**
: IP address of the device e.g. 192.168.1.123.

**Identifier**
: The device identifier of the box e.g. C42996000000

## Removal

This integration follows standard integration removal. No extra steps are required.

Go to "Settings > Devices & Services". Select Philips Hue Play HDMI Sync Box. Click the three dots ⋮ menu and then select Delete.
