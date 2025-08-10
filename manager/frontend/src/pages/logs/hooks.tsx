import { useState, useEffect } from 'react'

export function useCardContentHeight(cardRef: React.RefObject<HTMLDivElement>) {
  const [cardContentHeight, setCardContentHeight] = useState(0)

  const calcCardContentHeight = () => {
    if (cardRef.current) {
      const currentCard = cardRef.current
      const cardHight = currentCard.clientHeight
      const { paddingTop, paddingBottom, borderTopWidth, borderBottomWidth, gap } =
        window.getComputedStyle(currentCard, null)

      const { children } = currentCard
      let cardHeaderHeight = 0
      let cardFooterHeight = 0

      if (children.length > 1) {
        cardHeaderHeight = children[0].clientHeight
      }
      if (children.length > 2) {
        cardFooterHeight = children[2].clientHeight
      }

      let contentHeight =
        cardHight -
        parseFloat(paddingTop) -
        parseFloat(paddingBottom) -
        parseFloat(borderTopWidth) -
        parseFloat(borderBottomWidth) -
        cardHeaderHeight -
        cardFooterHeight -
        parseFloat(gap) -
        3 // pad

      if (cardFooterHeight > 0) {
        contentHeight -= parseFloat(gap)
      }

      setCardContentHeight(contentHeight)
    }
  }

  useEffect(() => {
    calcCardContentHeight()

    window.addEventListener('resize', calcCardContentHeight)

    return () => {
      window.removeEventListener('resize', calcCardContentHeight)
    }
  }, [cardRef.current, window.innerHeight])

  return cardContentHeight
}

export function useScrollToBottom(ref: React.RefObject<HTMLDivElement>, data: any[]) {
  useEffect(() => {
    if (ref.current && data.length > 0) {
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [ref.current, data])
}
