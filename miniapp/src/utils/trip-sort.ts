import type { TripStatus } from '../services/trip'

interface TripSortInput {
  status: TripStatus
  startDate: string | null
}

const completionSortGroup = (trip: TripSortInput) => (
  trip.status === 'completed' ? 1 : 0
)

export const tripDateSortValue = (trip: TripSortInput) => {
  if (!trip.startDate) return Number.MAX_SAFE_INTEGER

  const [year, month, day] = trip.startDate.split('-').map(Number)
  if (!year || !month || !day) return Number.MAX_SAFE_INTEGER

  return new Date(year, month - 1, day).getTime()
}

export const compareTripsForDisplay = (left: TripSortInput, right: TripSortInput) => {
  const completionCompare = completionSortGroup(left) - completionSortGroup(right)
  if (completionCompare !== 0) return completionCompare

  return tripDateSortValue(left) - tripDateSortValue(right)
}

export const sortTripsForDisplay = <T extends TripSortInput>(trips: T[]) => (
  trips
    .map((trip, index) => ({ trip, index }))
    .sort((left, right) => (
      compareTripsForDisplay(left.trip, right.trip) || left.index - right.index
    ))
    .map((item) => item.trip)
)
